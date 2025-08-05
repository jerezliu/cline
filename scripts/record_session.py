"""Script to run a headless chromium instance for automated testing.

Example:

```bash
# Set up virtual environment.
virtualenv venv
source venv/bin/activate
pip install playwright
playwright install chromium

# Execute the script.
python record_session.py

# Shut down the virtual environment.
deactivate
```

"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    """
    Launches Chromium, navigates to a URL, and records a 10-second video.
    """
    # The target URL you want to navigate to
    target_url = "http://127.0.0.1:8080/?folder=/home/jereliu/GitHub/test_app/"

    # The directory where the video will be saved
    video_save_dir = "videos/"

    # The duration of the recording in seconds
    record_duration_minutes = 1

    async with async_playwright() as p:
        # Launch the Chromium browser. 
        # 'headless=False' makes the browser window visible.
        # Set to 'headless=True' to run in the background.
        browser = await p.chromium.launch(headless=True)

        # Create a new browser context with video recording enabled.
        # The video recording starts immediately when the context is created.
        context = await browser.new_context(
            record_video_dir=video_save_dir,
            # Set a specific viewport size for consistent video dimensions
            viewport={"width": 1920, "height": 1080},
            # Grant clipboard permissions
            permissions=["clipboard-read", "clipboard-write"],            
        )

        # Create a new page within the context
        page = await context.new_page()

        print(f"Navigating to {target_url}...")
        try:
            # Go to the specified URL
            await page.goto(target_url, wait_until="domcontentloaded")
            
            print(f"Successfully navigated. Recording for {record_duration_minutes} minute(s)...")
            
            # Wait for 10 seconds while the video is being recorded.
            # You could perform other actions here instead of just waiting.
            await asyncio.sleep(record_duration_minutes * 60)

            print("Finished recording.")

        except Exception as e:
            print(f"An error occurred: {e}")
            print("Please ensure your local server is running at http://127.0.0.1:8080/")

        finally:
            # Closing the context will stop the recording and save the video file.
            # This is a crucial step! The video is not finalized until the context is closed.
            await context.close()
            await browser.close()
            
            print(f"Video saved in the '{video_save_dir}' directory.")
            print("The video file will have a random name and a .webm extension.")


if __name__ == "__main__":
    asyncio.run(main())
