import * as http from "http"
import * as vscode from "vscode"
import * as path from "path"
import { execa } from "execa"
import { Logger } from "@services/logging/Logger"
import { WebviewProvider } from "@core/webview"
import { AutoApprovalSettings } from "@shared/AutoApprovalSettings"
import { TaskServiceClient } from "webview-ui/src/services/grpc-client"
import { validateWorkspacePath, initializeGitRepository, getFileChanges, calculateToolSuccessRate } from "./GitHelper"
import { updateGlobalState, getAllExtensionState, storeSecret } from "@core/storage/state"
import { ClineAsk, ExtensionMessage, ClineMessage } from "@shared/ExtensionMessage"
import { ApiProvider } from "@shared/api"
import { HistoryItem } from "@shared/HistoryItem"
import { getSavedClineMessages, getSavedApiConversationHistory } from "@core/storage/disk"
import { AskResponseRequest } from "@shared/proto/cline/task"
import { getCwd } from "@/utils/path"

/**
 * Creates a tracker to monitor tool calls and failures during task execution
 * @param webviewProvider The webview provider instance
 * @returns Object tracking tool calls and failures
 */
function createToolCallTracker(webviewProvider: WebviewProvider): {
	toolCalls: Record<string, number>
	toolFailures: Record<string, number>
} {
	const tracker = {
		toolCalls: {} as Record<string, number>,
		toolFailures: {} as Record<string, number>,
	}

	// Intercept messages to track tool usage
	const originalPostMessageToWebview = webviewProvider.controller.postMessageToWebview
	webviewProvider.controller.postMessageToWebview = async (message: ExtensionMessage) => {
		// NOTE: Tool tracking via partialMessage has been migrated to gRPC streaming
		// This interceptor is kept for potential future use with other message types

		// Track tool calls - commented out as partialMessage is now handled via gRPC
		// if (message.type === "partialMessage" && message.partialMessage?.say === "tool") {
		// 	const toolName = (message.partialMessage.text as any)?.tool
		// 	if (toolName) {
		// 		tracker.toolCalls[toolName] = (tracker.toolCalls[toolName] || 0) + 1
		// 	}
		// }

		// Track tool failures - commented out as partialMessage is now handled via gRPC
		// if (message.type === "partialMessage" && message.partialMessage?.say === "error") {
		// 	const errorText = message.partialMessage.text
		// 	if (errorText && errorText.includes("Error executing tool")) {
		// 		const match = errorText.match(/Error executing tool: (\w+)/)
		// 		if (match && match[1]) {
		// 			const toolName = match[1]
		// 			tracker.toolFailures[toolName] = (tracker.toolFailures[toolName] || 0) + 1
		// 		}
		// 	}
		// }

		return originalPostMessageToWebview.call(webviewProvider.controller, message)
	}

	return tracker
}

/**
 * Starts an interval to blindly send "yesButtonClicked" responses.
 * This is used to automatically click any confirmation buttons that appear in the UI.
 * @param webviewProvider The webview provider instance.
 * @param waitSeconds The interval in seconds.
 * @returns The interval timer object.
 */
function startBlindApprovalInterval(webviewProvider: WebviewProvider, waitSeconds: number): NodeJS.Timeout {
	Logger.log(`Starting blind approval interval: clicking 'yes' every ${waitSeconds} seconds when in Act Mode.`)
	return setInterval(async () => {
		if (webviewProvider.controller?.task && webviewProvider.controller.task.mode === "act") {
			try {
				// Blindly send a "yes" response. This will succeed if an 'ask' is active,
				// and fail silently otherwise, which is the intended behavior.
				await webviewProvider.controller.task.handleWebviewAskResponse("yesButtonClicked")
				Logger.log(`Blindly sent yesButtonClicked response in Act Mode.`)
			} catch (error) {
				// This error is expected if no 'ask' is active. We can ignore it.
			}
		}
	}, waitSeconds * 1000)
}

// Task completion tracking
let taskCompletionResolver: (() => void) | null = null

// Function to create a new task completion promise
function createTaskCompletionTracker(): Promise<void> {
	// Create a new promise that will resolve when the task is completed
	return new Promise<void>((resolve) => {
		taskCompletionResolver = resolve
	})
}

// Function to mark the current task as completed
function completeTask(): void {
	if (taskCompletionResolver) {
		taskCompletionResolver()
		taskCompletionResolver = null
		Logger.log("Task marked as completed")
	}
}

let testServer: http.Server | undefined
let messageCatcherDisposable: vscode.Disposable | undefined
let blindApprovalInterval: NodeJS.Timeout | undefined

/**
 * Updates the auto approval settings to enable all actions
 * @param context The VSCode extension context
 * @param provider The webview provider instance
 */
async function updateAutoApprovalSettings(context: vscode.ExtensionContext, provider?: WebviewProvider) {
	try {
		const { autoApprovalSettings } = await getAllExtensionState(context)

		// Enable all actions
		const updatedSettings: AutoApprovalSettings = {
			...autoApprovalSettings,
			enabled: true,
			actions: {
				readFiles: true,
				readFilesExternally: true,
				editFiles: true,
				editFilesExternally: true,
				executeSafeCommands: true,
				executeAllCommands: true,
				useBrowser: true, // Enable browser for tests
				useMcp: true, // Enable MCP for tests
			},
			maxRequests: 10000, // Increase max requests for tests
		}

		await updateGlobalState(context, "autoApprovalSettings", updatedSettings)
		Logger.log("Auto approval settings updated for test mode")

		// Update the webview with the new state
		if (provider?.controller) {
			await provider.controller.postStateToWebview()
		}
	} catch (error) {
		Logger.log(`Error updating auto approval settings: ${error}`)
	}
}

/**
 * Creates and starts an HTTP server for test automation with Plan/Act mode support
 * @param webviewProvider The webview provider instance to use for message catching
 * @returns The created HTTP server instance
 */
export function createPlanActTestServer(webviewProvider?: WebviewProvider): http.Server {
	// Try to show the Cline sidebar
	Logger.log("[createPlanActTestServer] Opening Cline in sidebar...")
	vscode.commands.executeCommand("workbench.view.claude-dev-ActivityBar")

	// Then ensure the webview is focused/loaded
	vscode.commands.executeCommand("claude-dev.SidebarProvider.focus")

	// Update auto approval settings if webviewProvider is available
	if (webviewProvider?.controller?.context) {
		updateAutoApprovalSettings(webviewProvider.controller.context, webviewProvider)
	}
	const PORT = 9877 // Use a different port for PlanActTestServer

	testServer = http.createServer((req, res) => {
		// Set CORS headers
		res.setHeader("Access-Control-Allow-Origin", "*")
		res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS")
		res.setHeader("Access-Control-Allow-Headers", "Content-Type")

		// Handle preflight requests
		if (req.method === "OPTIONS") {
			res.writeHead(204)
			res.end()
			return
		}

		// Handle shutdown request
		if (req.method === "POST" && req.url === "/shutdown") {
			res.writeHead(200)
			res.end(JSON.stringify({ success: true, message: "Server shutting down" }))

			// Shut down the server after sending the response
			setTimeout(() => {
				shutdownPlanActTestServer()
			}, 100)

			return
		}

		// Only handle POST requests to /task
		if (req.method !== "POST" || req.url !== "/task") {
			res.writeHead(404)
			res.end(JSON.stringify({ error: "Not found" }))
			return
		}

		// Parse the request body
		let body = ""
		req.on("data", (chunk) => {
			body += chunk.toString()
		})

		req.on("end", async () => {
			try {
				// Parse the JSON body
				const { task, apiKey, apiProvider = "gemini", waitSeconds = 10 } = JSON.parse(body)

				if (!task) {
					res.writeHead(400)
					res.end(JSON.stringify({ error: "Missing task parameter" }))
					return
				}

				// Get a visible webview instance
				const visibleWebview = WebviewProvider.getVisibleInstance()
				if (!visibleWebview || !visibleWebview.controller) {
					res.writeHead(500)
					res.end(JSON.stringify({ error: "No active Cline instance found" }))
					return
				}

				// Initiate a new task
				Logger.log(`PlanActTestServer initiating task: ${task}`)

				try {
					// Get and validate the workspace path
					const workspacePath = await getCwd()
					Logger.log(`Using workspace path: ${workspacePath}`)

					// Validate workspace path before proceeding with any operations
					try {
						await validateWorkspacePath(workspacePath)
					} catch (error) {
						Logger.log(`Workspace validation failed: ${error.message}`)
						res.writeHead(500)
						res.end(
							JSON.stringify({
								error: `Workspace validation failed: ${error.message}. Please open a workspace folder in VSCode before running the test.`,
								workspacePath,
							}),
						)
						return
					}

					// Initialize Git repository before starting the task
					try {
						const wasNewlyInitialized = await initializeGitRepository(workspacePath)
						if (wasNewlyInitialized) {
							Logger.log(`Initialized new Git repository in ${workspacePath} before task start`)
						} else {
							Logger.log(`Using existing Git repository in ${workspacePath} before task start`)
						}

						// Log directory contents before task start
						try {
							const { stdout: lsOutput } = await execa("ls", ["-la", workspacePath])
							Logger.log(`Directory contents before task start:\n${lsOutput}`)
						} catch (lsError) {
							Logger.log(`Warning: Failed to list directory contents: ${lsError.message}`)
						}
					} catch (gitError) {
						Logger.log(`Warning: Git initialization failed: ${gitError.message}`)
						Logger.log("Continuing without Git initialization")
					}

					// Clear any existing task
					await visibleWebview.controller.clearTask()

					// If API key is provided, update the API configuration
					if (apiKey) {
						Logger.log("API key provided, updating API configuration")

						// Get current API configuration
						const { apiConfiguration } = await getAllExtensionState(visibleWebview.controller.context)

						// Update API configuration with API key
						// TODO: support LiteLLM as provider.
						const updatedConfig = {
							...apiConfiguration,
							apiProvider: apiProvider as ApiProvider,
							geminiApiKey: apiKey,
						}

						// Store the API key securely
						await storeSecret(visibleWebview.controller.context, "geminiApiKey", apiKey)

						visibleWebview.controller.cacheService.setApiConfiguration(updatedConfig)

						// Update cache service to use cline provider
						const currentConfig = visibleWebview.controller.cacheService.getApiConfiguration()
						visibleWebview.controller.cacheService.setApiConfiguration({
							...currentConfig,
							planModeApiProvider: apiProvider,
							actModeApiProvider: apiProvider,
						})

						// Post state to webview to reflect changes
						await visibleWebview.controller.postStateToWebview()
					}

					// Ensure we're in Plan mode before initiating the task
					const { mode } = await visibleWebview.controller.getStateToPostToWebview()
					if (mode === "act") {
						// Switch to Plan mode if currently in Act mode
						await visibleWebview.controller.togglePlanActMode("plan")
					}

					// Initialize tool call tracker
					const toolTracker = createToolCallTracker(visibleWebview)

					// Record task start time
					const taskStartTime = Date.now()

					// Initiate the new task
					const result = await visibleWebview.controller.initTask(task)

					// Start the blind approval interval
					blindApprovalInterval = startBlindApprovalInterval(visibleWebview, waitSeconds)

					// Try to get the task ID directly from the result or from the state
					let taskId: string | undefined

					if (typeof result === "string") {
						// If initTask returns the task ID directly
						taskId = result
					} else {
						// Wait a moment for the state to update
						await new Promise((resolve) => setTimeout(resolve, 1000))

						// Try to get the task ID from the controller's state
						const state = await visibleWebview.controller.getStateToPostToWebview()
						taskId = state.currentTaskItem?.id

						// If still not found, try polling a few times
						if (!taskId) {
							for (let i = 0; i < 5; i++) {
								await new Promise((resolve) => setTimeout(resolve, 500))
								const updatedState = await visibleWebview.controller.getStateToPostToWebview()
								taskId = updatedState.currentTaskItem?.id
								if (taskId) {
									break
								}
							}
						}
					}

					if (!taskId) {
						throw new Error("Failed to get task ID after initiating task")
					}

					Logger.log(`Task initiated with ID: ${taskId}`)

					// Create a completion tracker for this task
					const completionPromise = createTaskCompletionTracker()

					// Wait for the task to complete with a timeout
					const timeoutPromise = new Promise<void>((_, reject) => {
						setTimeout(() => reject(new Error("Task completion timeout")), 30 * 60 * 1000) // 30 minute timeout
					})

					try {
						// Wait for either completion or timeout
						await Promise.race([completionPromise, timeoutPromise])

						// Get task history and metrics
						const taskHistory = await visibleWebview.controller.getStateToPostToWebview()
						const taskData = taskHistory.taskHistory?.find((t: HistoryItem) => t.id === taskId)

						// Get messages and API conversation history
						let messages: any[] = []
						let apiConversationHistory: any[] = []
						try {
							if (typeof taskId === "string") {
								messages = await getSavedClineMessages(visibleWebview.controller.context, taskId)
							}
						} catch (error) {
							Logger.log(`Error getting saved Cline messages: ${error}`)
						}

						try {
							if (typeof taskId === "string") {
								apiConversationHistory = await getSavedApiConversationHistory(
									visibleWebview.controller.context,
									taskId,
								)
							}
						} catch (error) {
							Logger.log(`Error getting saved API conversation history: ${error}`)
						}

						// Get file changes
						let fileChanges
						try {
							// Get the workspace path using our helper function
							const workspacePath = await getCwd()
							Logger.log(`Getting file changes from workspace path: ${workspacePath}`)

							// Log directory contents for debugging
							try {
								const { stdout: lsOutput } = await execa("ls", ["-la", workspacePath])
								Logger.log(`Directory contents after task completion:\n${lsOutput}`)
							} catch (lsError) {
								Logger.log(`Warning: Failed to list directory contents: ${lsError.message}`)
							}

							// Get file changes using Git
							fileChanges = await getFileChanges(workspacePath)

							// If no changes were detected, use a fallback method
							if (!fileChanges.created.length && !fileChanges.modified.length && !fileChanges.deleted.length) {
								Logger.log("No changes detected by Git, using fallback directory scan")

								// Try to get a list of all files in the directory
								try {
									const { stdout: findOutput } = await execa("find", [
										workspacePath,
										"-type",
										"f",
										"-not",
										"-path",
										"*/.*",
										"-not",
										"-path",
										"*/node_modules/*",
									])
									const files = findOutput.split("\n").filter(Boolean)

									// Add all files as "created" since we can't determine which ones are new
									fileChanges.created = files.map((file) => path.relative(workspacePath, file))
									Logger.log(`Fallback found ${fileChanges.created.length} files`)
								} catch (findError) {
									Logger.log(`Warning: Fallback directory scan failed: ${findError.message}`)
								}
							}
						} catch (fileChangeError) {
							Logger.log(`Error getting file changes: ${fileChangeError.message}`)
							throw new Error(`Error getting file changes: ${fileChangeError.message}`)
						}

						// Get tool metrics
						const toolMetrics = {
							toolCalls: toolTracker.toolCalls,
							toolFailures: toolTracker.toolFailures,
							totalToolCalls: Object.values(toolTracker.toolCalls).reduce((a, b) => a + b, 0),
							totalToolFailures: Object.values(toolTracker.toolFailures).reduce((a, b) => a + b, 0),
							toolSuccessRate: calculateToolSuccessRate(toolTracker.toolCalls, toolTracker.toolFailures),
						}

						// Calculate task duration
						const taskDuration = Date.now() - taskStartTime

						// Return comprehensive response with all metrics and data
						res.writeHead(200, { "Content-Type": "application/json" })
						res.end(
							JSON.stringify({
								success: true,
								taskId,
								completed: true,
								metrics: {
									tokensIn: taskData?.tokensIn || 0,
									tokensOut: taskData?.tokensOut || 0,
									cost: taskData?.totalCost || 0,
									duration: taskDuration,
									...toolMetrics,
								},
								messages,
								apiConversationHistory,
								files: fileChanges,
							}),
						)
					} catch (timeoutError) {
						// Task didn't complete within the timeout period
						res.writeHead(200, { "Content-Type": "application/json" })
						res.end(
							JSON.stringify({
								success: true,
								taskId,
								completed: false,
								timeout: true,
							}),
						)
					}
				} catch (error) {
					Logger.log(`Error initiating task: ${error}`)
					res.writeHead(500)
					res.end(JSON.stringify({ error: `Failed to initiate task: ${error}` }))
				}
			} catch (error) {
				res.writeHead(400)
				res.end(JSON.stringify({ error: `Invalid JSON: ${error}` }))
			}
		})
	})

	testServer.listen(PORT, () => {
		Logger.log(`PlanActTestServer listening on port ${PORT}`)
	})

	// Handle server errors
	testServer.on("error", (error) => {
		Logger.log(`PlanActTestServer error: ${error}`)
	})

	// Set up message catcher for the provided webview instance or try to get the visible one
	if (webviewProvider) {
		messageCatcherDisposable = createMessageCatcher(webviewProvider)
	} else {
		const visibleWebview = WebviewProvider.getVisibleInstance()
		if (visibleWebview) {
			messageCatcherDisposable = createMessageCatcher(visibleWebview)
		} else {
			Logger.log("No visible webview instance found for message catcher")
		}
	}

	return testServer
}

/**
 * Checks for the end of the planning phase and automatically switches to Act mode.
 * @param planModeState An object containing the flag to track if the initial plan response has been received.
 * @param webviewProvider The webview provider instance.
 * @param innerMessage The inner Cline message from the gRPC response.
 */
async function handlePlanToActTransition(
	planModeState: { received: boolean },
	webviewProvider: WebviewProvider,
	innerMessage: ClineMessage | undefined,
): Promise<void> {
	const shouldEvaluate =
		!planModeState.received &&
		webviewProvider.controller &&
		(await webviewProvider.controller.getStateToPostToWebview()).mode === "plan" &&
		innerMessage &&
		((innerMessage.say as any) === 4 || (innerMessage.ask as any) === 1) && // "text" is enum 4; "plan_mode_respond" is enum 1.
		!innerMessage.partial

	if (!shouldEvaluate) {
		return
	}

	try {
		// Further examine if the complete text response is a tool call.
		const toolCall = JSON.parse(innerMessage.text || "{}")
		const toolName = toolCall.tool
		// If the response is complete text and not a function call, then likely indicating the end of planning mode.
		if (!toolName) {
			planModeState.received = true // Set the flag to prevent multiple switches
			Logger.log(`Non-tool response detected in Plan mode. Automatically switching to Act mode.`)
			setTimeout(async () => {
				try {
					if (webviewProvider.controller) {
						await webviewProvider.controller.togglePlanActMode("act")
						Logger.log("Successfully switched to Act mode.")
					}
				} catch (error) {
					Logger.log(`Error automatically switching to Act mode: ${error}`)
				}
			}, 500) // Delay to ensure the message is processed before switching
		}
	} catch (error) {
		Logger.log(`Error parsing tool call message: ${error}`)
		// NOTE: The original logic did not switch to Act mode if JSON.parse failed.
		// This is preserved, but might be worth revisiting as a non-JSON response
		// is likely the end of the plan.
	}
}

/**
 * Handles 'command_output' ask messages by automatically clicking "Proceed While Running" after a delay.
 * @param webviewProvider The webview provider instance.
 * @param innerMessage The inner Cline message from the gRPC response.
 * @param timeoutSeconds The delay in seconds before responding. Defaults to 3.
 */
function handleToolCallDelay(webviewProvider: WebviewProvider, innerMessage: ClineMessage | undefined, timeoutSeconds = 3): void {
	if (!innerMessage || innerMessage.partial || !webviewProvider.controller?.task) {
		return
	}

	const messageType = innerMessage.type as any
	if (messageType === 0) {
		// "ask"
		const askType = innerMessage.ask as any
		if (askType === 3) {
			// "command_output"
			Logger.log(`Command output detected. Auto-responding in ${timeoutSeconds} seconds...`)
			setTimeout(async () => {
				try {
					await webviewProvider.controller?.task?.handleWebviewAskResponse("yesButtonClicked")
					Logger.log(`Auto-responded to command_output with yesButtonClicked`)
				} catch (error) {
					Logger.log(`Error sending askResponse for command_output: ${error}`)
				}
			}, timeoutSeconds * 1000)
		}
	}
}

/**
 * Checks for the task completion message and marks the task as complete.
 * @param webviewProvider The webview provider instance.
 * @param innerMessage The inner Cline message from the gRPC response.
 */
async function handleTaskCompletion(webviewProvider: WebviewProvider, innerMessage: ClineMessage | undefined): Promise<void> {
	const shouldComplete =
		innerMessage &&
		(innerMessage.say as any) === 6 && // "completion_result" is enum 6
		!innerMessage.partial

	if (shouldComplete) {
		Logger.log("Completion result received. Switching to plan mode and marking task as complete.")
		if (webviewProvider.controller) {
			await webviewProvider.controller.togglePlanActMode("plan")
		}
		completeTask()
	}
}

/**
 * Handles command-related 'ask' messages by automatically responding after a delay.
 * This includes standard commands and MCP tool calls that execute commands.
 * @param webviewProvider The webview provider instance.
 * @param innerMessage The inner Cline message from the gRPC response.
 * @param timeoutSeconds The delay in seconds before responding. Defaults to 3.
 */
function handleCommandMessage(
	webviewProvider: WebviewProvider,
	innerMessage: ClineMessage | undefined,
	timeoutSeconds = 3,
): void {
	if (!innerMessage || innerMessage.partial || !webviewProvider.controller?.task) {
		return
	}

	let askTypeName = ""
	let shouldRespond = false
	const messageType = innerMessage.type as any

	if (messageType === 0) {
		// "ask"
		const askType = innerMessage.ask as any
		if (askType === 2) {
			// "command"
			shouldRespond = true
			askTypeName = "command"
		} else if (askType === 12) {
			// "use_mcp_server"
			shouldRespond = true
			askTypeName = "use_mcp_server"
		}
	} else if (messageType === 1) {
		// "say"
		const sayType = innerMessage.say as any
		if (sayType === 12) {
			// "tool"
			// As discussed, 'say' messages don't have a button to click.
			// We will just log it as requested.
			try {
				const toolInfo = JSON.parse(innerMessage.text || "{}")
				Logger.log(`Tool execution announced: ${toolInfo.tool || "unknown tool"}`)
			} catch {
				Logger.log(`Tool execution announced with non-JSON text: ${innerMessage.text}`)
			}
			shouldRespond = true
			askTypeName = "tool"
		} else if (sayType === 10) {
			// "command"
			shouldRespond = true
			askTypeName = "command"
		}
	}

	if (shouldRespond) {
		Logger.log(`Command-like message ('${askTypeName}') detected. Auto-responding in ${timeoutSeconds} seconds...`)
		setTimeout(async () => {
			try {
				await webviewProvider.controller?.task?.handleWebviewAskResponse("yesButtonClicked")
				Logger.log(`Auto-responded to ${askTypeName} ask with yesButtonClicked`)
			} catch (error) {
				Logger.log(`Error sending askResponse for ${askTypeName}: ${error}`)
			}
		}, timeoutSeconds * 1000)
	}
}

/**
 * Creates a message catcher that logs all messages sent to the webview
 * and automatically responds to messages that require user intervention
 * @param webviewProvider The webview provider instance
 * @returns A disposable that can be used to clean up the message catcher
 */
export function createMessageCatcher(webviewProvider: WebviewProvider): vscode.Disposable {
	Logger.log("Cline message catcher registered")

	if (webviewProvider && webviewProvider.controller) {
		const originalPostMessageToWebview = webviewProvider.controller.postMessageToWebview
		const planModeState = { received: false } // Flag to track if the initial plan response has been received

		// Intercept outgoing messages from extension to webview
		webviewProvider.controller.postMessageToWebview = async (message: ExtensionMessage) => {
			// NOTE: Completion and ask message detection has been migrated to gRPC streaming
			// This interceptor is kept for potential future use with other message types

			const innerMessage = message.grpc_response?.message as ClineMessage | undefined
			if (innerMessage?.partial !== undefined) {
				Logger.log(`=======================`)
				Logger.log(`innerMessage received.`)
				Logger.log(`planModeResponseReceived:${planModeState.received}; BOOL: ${!planModeState.received}`)
				Logger.log(
					`mode:${(await webviewProvider.controller.getStateToPostToWebview()).mode}; BOOL: ${
						(await webviewProvider.controller.getStateToPostToWebview()).mode === "plan"
					}`,
				)
				Logger.log(`innerMessage.type:${innerMessage?.type}; BOOL: ${(innerMessage?.type as any) === "ask"}`)
				Logger.log(`innerMessage.ask:${innerMessage?.ask}; BOOL: ${(innerMessage?.ask as any) === 2};`)
				Logger.log(`innerMessage.say:${innerMessage?.say}; BOOL: ${(innerMessage?.say as any) === 4};`)
				Logger.log(`TEXT: ${innerMessage?.text}`)
				Logger.log(`innerMessage.partial:${innerMessage?.partial};  BOOL: ${!innerMessage?.partial}`)
			}

			// Automatically switch to Act mode when a non-tool response is received in Plan mode.
			await handlePlanToActTransition(planModeState, webviewProvider, innerMessage)

			// Check for completion_result message and complete the task
			await handleTaskCompletion(webviewProvider, innerMessage)

			// Handle command ask messages
			handleCommandMessage(webviewProvider, innerMessage)

			// Handle tool call delay for "Proceed While Running"
			handleToolCallDelay(webviewProvider, innerMessage)

			return originalPostMessageToWebview.call(webviewProvider.controller, message)
		}
	} else {
		Logger.log("No visible webview instance found for message catcher")
	}

	return new vscode.Disposable(() => {
		// Cleanup function if needed
		Logger.log("Cline message catcher disposed")
	})
}

/**
 * Shuts down the test server if it exists
 */
export function shutdownPlanActTestServer() {
	if (testServer) {
		testServer.close()
		Logger.log("PlanActTestServer shut down")
		testServer = undefined
	}

	// Dispose of the message catcher if it exists
	if (messageCatcherDisposable) {
		messageCatcherDisposable.dispose()
		messageCatcherDisposable = undefined
	}

	// Clear the blind approval interval if it exists
	if (blindApprovalInterval) {
		clearInterval(blindApprovalInterval)
		blindApprovalInterval = undefined
		Logger.log("Blind approval interval stopped.")
	}
}
