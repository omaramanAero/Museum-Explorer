import sys, asyncio
from playwright.async_api import async_playwright
OUT=sys.argv[1]
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
    async def run(name, url, vw, vh, actions=None, full=False, scheme='light', dsf=2, clip=None):
      ctx=await b.new_context(viewport={'width':vw,'height':vh}, device_scale_factor=dsf, color_scheme=scheme)
      pg=await ctx.new_page()
      await pg.goto('http://localhost:8765/'+url)
      try: await pg.wait_for_function("!document.querySelector('model-viewer') || document.querySelector('model-viewer').loaded", timeout=60000)
      except Exception: print(name,'mv not loaded')
      await pg.wait_for_timeout(2200)
      if actions: await actions(pg)
      await pg.screenshot(path=f'{OUT}/{name}.png', full_page=full, clip=clip)
      await ctx.close()
    async def anatomy(pg):
      await pg.click('#anatomyBtn'); await pg.wait_for_timeout(800)
      await pg.click('model-viewer .mek-hotspot[data-i="0"]', force=True); await pg.wait_for_timeout(2000)
    async def anatomy5(pg):
      await pg.click('#anatomyBtn'); await pg.wait_for_timeout(800)
      await pg.click('model-viewer .mek-hotspot[data-i="4"]', force=True); await pg.wait_for_timeout(2000)
    async def de(pg):
      await pg.click('#lang-de'); await pg.wait_for_timeout(2500)
    async def glide(pg):
      await pg.click('[data-anim="Glide"]'); await pg.wait_for_timeout(3000)
    await run('p_home','index.html',390,844)
    await run('p_ex1','index.html#EX01',390,844)
    await run('p_ex1_scroll','index.html#EX01',390,844, lambda pg: pg.evaluate("window.scrollTo(0, 250)"))
    await run('p_ex1_anat','index.html#EX01',390,844,anatomy)
    await run('p_ex1_anat5','index.html#EX01',390,844,anatomy5)
    await run('p_ex1_de','index.html#EX01',390,844,de)
    await run('p_ex2','index.html#EX02',390,844)
    await run('p_ex3','index.html#EX03',390,844)
    await run('d_ex1','index.html#EX01',1360,860, glide, dsf=1.5)
    await run('d_ex1_anat','index.html#EX01',1360,860, anatomy, dsf=1.5)
    await run('d_ex3_maps','index.html#EX03',1360,860, lambda pg: pg.evaluate("document.getElementById('h-maps').scrollIntoView()"), dsf=1.5)
    await run('d_home','index.html',1360,860, dsf=1.5)
    await run('cards','cards.html?base=https%3A%2F%2Fclaude.ai%2Fartifact%2FDsgFoU4sneqqty2qjDDPUW',900,760, full=True, dsf=2)
    await b.close()
asyncio.run(main())
