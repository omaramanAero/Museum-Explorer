import sys, asyncio
from playwright.async_api import async_playwright
OUT=sys.argv[1]
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
    async def run(name, url, vw, vh, actions=None, full=False, scheme='light', dsf=1):
      ctx=await b.new_context(viewport={'width':vw,'height':vh}, device_scale_factor=dsf, color_scheme=scheme)
      pg=await ctx.new_page()
      pg.on('console', lambda m: print(name,'console:', m.type, m.text) if m.type=='error' and 'fonts.g' not in m.text and 'ERR_' not in m.text else None)
      pg.on('pageerror', lambda e: print(name,'PAGEERROR', e))
      await pg.goto('http://localhost:8765/'+url)
      try: await pg.wait_for_function("!document.querySelector('model-viewer') || document.querySelector('model-viewer').loaded", timeout=60000)
      except Exception: print(name,'mv not loaded')
      await pg.wait_for_timeout(1800)
      if actions: await actions(pg)
      await pg.screenshot(path=f'{OUT}/{name}.png', full_page=full)
      await ctx.close()
    async def anatomy(pg):
      await pg.click('#anatomyBtn'); await pg.wait_for_timeout(800)
      await pg.click('model-viewer .mek-hotspot[data-i="4"]', force=True); await pg.wait_for_timeout(1800)
    async def glide(pg):
      await pg.click('[data-anim="Glide"]'); await pg.wait_for_timeout(2500)
    await run('home_m','index.html',390,844,full=True, dsf=2)
    await run('ex1_m','index.html#EX01',390,844, dsf=2)
    await run('ex1_anat_m','index.html#EX01',390,844,anatomy, dsf=2)
    await run('ex1_d','index.html#EX01',1360,860)
    await run('ex1_glide_d','index.html#EX01',1360,860,glide)
    await run('ex1_anat_d','index.html#EX01',1360,860,anatomy)
    await run('ex1_dark_d','index.html#EX01',1360,860, scheme='dark')
    await run('ex2_d','index.html#EX02',1360,860)
    await run('ex3_d','index.html#EX03',1360,860, full=True)
    await run('home_d','index.html',1360,860, full=True)
    await b.close()
asyncio.run(main())
