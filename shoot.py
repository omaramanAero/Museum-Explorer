import sys, asyncio
from playwright.async_api import async_playwright
OUT=sys.argv[1]; shots=[a.split('|') for a in sys.argv[2:]]
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
    pg=await b.new_page(viewport={'width':800,'height':600})
    pg.on('console', lambda m: print('console:', m.text) if m.type in ('error','warning') else None)
    for name,url in shots:
      await pg.goto('http://localhost:8765/'+url)
      try: await pg.wait_for_function("document.title==='ready'", timeout=30000)
      except Exception as e: print('timeout', name)
      await pg.wait_for_timeout(500)
      await pg.screenshot(path=f'{OUT}/{name}.png')
    await b.close()
asyncio.run(main())
