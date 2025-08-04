#!/usr/bin/env node
import axios from "axios"
import * as path from "path"
import * as fs from "fs"
import { program } from "commander"

program
	.name("run-plan-act-test")
	.description("CLI to run a Plan/Act mode test with Cline")
	.option("-t, --task <string>", "The task to send to Cline")
	.option("-k, --api-key <string>", "The API key for Cline")
	.option("-w, --workspace <string>", "The workspace path for the test")
	.option("-r, --results-filename <string>", "The filename for the results JSON file")
	.option(
		"--blind-approval-wait-seconds <number>",
		"The number of seconds to wait before automatically approving a tool call",
	)
	.option("--timeout-minutes <number>", "The overall timeout in minutes for the task", "15")
	.action(async (options) => {
		const { task, apiKey, workspace, resultsFilename, blindApprovalWaitSeconds, timeoutMinutes } = options

		if (!task) {
			console.error("Error: --task is required.")
			program.help()
			return
		}

		if (!workspace) {
			console.error("Error: --workspace is required.")
			program.help()
			return
		}

		const serverUrl = "http://localhost:9877" // PlanActTestServer runs on port 9877
		let exitCode = 0

		try {
			console.log(`Sending task to Cline PlanActTestServer: "${task}"`)
			console.log(`Using workspace: "${workspace}"`)

			// Ensure the workspace directory exists
			if (!fs.existsSync(workspace)) {
				console.error(`Error: Workspace directory not found at ${workspace}`)
				process.exit(1)
			}

			// Send the task to the test server
			const requestBody: { task: string; apiKey?: string; waitSeconds?: number; resultsFilename?: string } = {
				task,
			}
			if (apiKey) {
				requestBody.apiKey = apiKey
			}
			if (blindApprovalWaitSeconds) {
				requestBody.waitSeconds = parseInt(blindApprovalWaitSeconds, 10)
			}
			if (resultsFilename) {
				requestBody.resultsFilename = resultsFilename
			}
			const response = await axios.post(`${serverUrl}/task`, requestBody, {
				headers: {
					"Content-Type": "application/json",
				},
				timeout: parseInt(timeoutMinutes, 10) * 60 * 1000,
			})

			if (response.data.resultsPath) {
				console.log(`Results saved to: ${response.data.resultsPath}`)
			}

			if (response.data.success && response.data.completed) {
				console.log("Task completed successfully!")
				exitCode = 0
			} else if (response.data.success && response.data.timeout) {
				console.warn("Task timed out before completion.")
				exitCode = 1
			} else {
				console.error("Task failed or did not complete successfully.")
				exitCode = 1
			}
		} catch (error) {
			if (axios.isAxiosError(error)) {
				console.error(`Error communicating with Cline PlanActTestServer: ${error.message}`)
				console.error(`Did you properly set vscode work directory?`)
				if (error.response) {
					console.error("Server responded with:", JSON.stringify(error.response.data, null, 2))
				}
			} else {
				console.error("An unexpected error occurred:", error)
			}
			exitCode = 1
		} finally {
			// Always try to shut down the server
			try {
				console.log("Requesting server shutdown...")
				await axios.post(`${serverUrl}/shutdown`, {}, { timeout: 5000 })
				console.log("Server shutdown request sent successfully.")
			} catch (shutdownError) {
				if (axios.isAxiosError(shutdownError)) {
					console.error(`Error sending shutdown request: ${shutdownError.message}`)
				} else {
					console.error("An unexpected error occurred during shutdown:", shutdownError)
				}
			}
			process.exit(exitCode)
		}
	})

program.parse(process.argv)
