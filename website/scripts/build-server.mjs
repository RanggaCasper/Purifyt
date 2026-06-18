import { copyFileSync, existsSync, mkdirSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { spawnSync } from 'node:child_process'

const root = resolve(import.meta.dirname, '..', '..')
const serverExe = resolve(root, 'dist', process.platform === 'win32' ? 'purifyt-server.exe' : 'purifyt-server')
const targetTriple = process.platform === 'win32' ? 'x86_64-pc-windows-msvc' : process.arch
const sidecar = resolve(
  root,
  'website',
  'src-tauri',
  'binaries',
  `purifyt-server-${targetTriple}${process.platform === 'win32' ? '.exe' : ''}`
)

function run(command, args) {
  const result = spawnSync(command, args, {
    cwd: root,
    stdio: 'inherit',
    shell: process.platform === 'win32'
  })

  if (result.status !== 0) {
    throw new Error(`${command} ${args.join(' ')} failed`)
  }
}

if (!existsSync(serverExe)) {
  run('python', ['-m', 'PyInstaller', 'purifyt.spec'])
}

if (!existsSync(serverExe)) {
  throw new Error(`Server binary not found: ${serverExe}`)
}

mkdirSync(dirname(sidecar), { recursive: true })
copyFileSync(serverExe, sidecar)
console.log(`Bundled Purifyt server sidecar: ${sidecar}`)
