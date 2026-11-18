import {readFileSync} from 'node:fs'
import assert from 'node:assert/strict'
import {build} from 'esbuild'
const before=readFileSync('../../desktop/plugin.js')
await build({entryPoints:['../../desktop/src/index.mjs'],bundle:true,outfile:'../../desktop/plugin.js',format:'esm',platform:'browser',minify:true,external:['react','react/jsx-runtime','@hermes/plugin-sdk']})
if(process.argv.includes('--check'))assert.deepEqual(readFileSync('../../desktop/plugin.js'),before,'committed plugin must match source build')
