"""Script to run a headless chromium instance to invoke cline client session."""
import asyncio
import argparse
from playwright.async_api import async_playwright

async def main(url: str, workspace: str, record: bool):
    """
    Launches Chromium, navigates to a URL, and optionally records a video.
    """
    target_url = f"{url}/?folder={workspace}"
    
    context_args = {
        "viewport": {"width": 1920, "height": 1080},
        "permissions": ["clipboard-read", "clipboard-write"],
    }
    if record:
        video_save_dir = f"{workspace}/videos/"
        context_args["record_video_dir"] = video_save_dir
        print(f"Session recording video will be saved in the '{video_save_dir}' directory.")


    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(**context_args)
        page = await context.new_page()

        print(f"Navigating to {target_url}...")
        try:
            await page.goto(target_url, wait_until="domcontentloaded")
            print("Successfully navigated. Recording indefinitely...")
            print("Script will be terminated by the parent process.")
            # Keep the script running until it's externally terminated
            await asyncio.Event().wait()

        except asyncio.CancelledError:
            print("\nRecording task was cancelled. Saving video...")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            await context.close()
            await browser.close()
            if record:
                print(f"Video saved in the '{video_save_dir}' directory.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Record a browser session with Playwright.")
    parser.add_argument("--url", required=True, help="The URL to navigate to.")
    parser.add_argument("--dir", required=True, help="The project directory to initiate vscode at.")
    parser.add_argument("--record", action="store_true", help="Enable video recording.")
    args = parser.parse_args()

    try:
        asyncio.run(main(args.url, args.dir, args.record))
    except KeyboardInterrupt:
        print("\nScript interrupted by user.")
