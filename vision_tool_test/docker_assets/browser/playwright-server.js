const { chromium } = require("playwright");
// Read ws path from environment variable
const wsPath = process.env.WS_PATH || "default";
const port = process.env.PLAYWRIGHT_PORT || 37367;

(async () => {
  console.log("Starting Playwright server...");

  // Start the remote debugging server
  const browserServer = await chromium.launchServer({
    headless: false,
    port: port,
    wsPath: wsPath,
    // Bind to all interfaces (Playwright default, but explicit for safety)
    args: [
        '--start-fullscreen',
        '--start-maximized',
        '--window-size=1440,1440',
        '--window-position=0,0',
        '--disable-infobars',
        '--no-default-browser-check',
        '--kiosk',
        '--disable-session-crashed-bubble',
        '--noerrdialogs',
        '--force-device-scale-factor=1.0',
        '--disable-features=DefaultViewportMetaTag',
        '--force-device-width=1440',
        '--remote-debugging-address=0.0.0.0',  // Ensure binding to 0.0.0.0
    ],
  });

  console.log(`Playwright server listening on port ${port} with path /${wsPath}`);

  // Keep the process running
  process.on("SIGINT", async () => {
    console.log("Shutting down Playwright server...");
    // await browser.close();
    await browserServer.close();
    process.exit(0);
  });
})();
