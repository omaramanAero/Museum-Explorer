import sys, asyncio
from playwright.async_api import async_playwright
OUT=sys.argv[1]
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
    async def run(name, url, vw, vh, actions=None, dsf=1.5, clip=None):
      ctx=await b.new_context(viewport={'width':vw,'height':vh}, device_scale_factor=dsf)
      pg=await ctx.new_page(); await pg.goto('http://localhost:8765/'+url)
      try: await pg.wait_for_function("!document.querySelector('model-viewer') || document.querySelector('model-viewer').loaded", timeout=60000)
      except Exception: print(name,'mv not loaded')
      await pg.wait_for_timeout(2000)
      if actions: await actions(pg)
      await pg.screenshot(path=f'{OUT}/{name}.png', clip=clip)
      await ctx.close()
    async def tomaps(pg):
      await pg.evaluate("document.getElementById('h-maps').scrollIntoView({block:'start'})"); await pg.wait_for_timeout(500)
    await run('d_ex1_maps','index.html#EX01',1100,620, tomaps, dsf=2, clip={'x':120,'y':40,'width':700,'height':560})
    await run('p_ex3b','index.html#EX03',390,844, dsf=2)
    await run('p_ex1_de2','index.html#EX01',390,844, lambda pg: pg.click('#lang-de'), dsf=2)
    await b.close()
asyncio.run(main())
