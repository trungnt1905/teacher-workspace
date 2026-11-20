// Guards the design system (docs/design-system.md): every screen must use the shared tokens so that
// colours stay consistent as new features are added.
import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

const root = path.resolve(__dirname, '../..')
const tokensCss = fs.readFileSync(path.join(root, 'resources/css/tokens.css'), 'utf8')
const defined = new Set([...tokensCss.matchAll(/(--[\w-]+)\s*:/g)].map((m) => m[1]))
const palette = new Set([...defined].filter((t) => /^--(gray|blue|red|green|amber)-\d+$/.test(t)))

function files(dir, ext) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    const p = path.join(dir, e.name)
    return e.isDirectory() ? files(p, ext) : p.endsWith(ext) ? [p] : []
  })
}

const sources = [
  ...files(path.join(root, 'resources/js'), '.vue'),
  path.join(root, 'resources/css/base.css'),
  path.join(root, 'resources/css/components.css'),
].map((f) => ({ file: path.relative(root, f), text: fs.readFileSync(f, 'utf8') }))

function styleOf(text, file) {
  if (!file.endsWith('.vue')) return text
  return [...text.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/g)].map((m) => m[1]).join('\n')
}

describe('design system', () => {
  it('has semantic colour tokens', () => {
    for (const t of ['--color-primary', '--color-action', '--color-warning', '--color-danger', '--color-success', '--color-surface', '--color-text']) {
      expect(defined.has(t), t).toBe(true)
    }
  })

  it.each(sources.map((s) => [s.file, s]))('%s uses no raw colours', (_, { file, text }) => {
    const css = styleOf(text, file)
    expect(css.match(/#[0-9a-fA-F]{3,8}\b/g) ?? [], 'hex colour — use a --color-* token').toEqual([])
    expect(css.match(/\brgba?\(/g) ?? [], 'rgb() — use a --color-* / --shadow-* token').toEqual([])
  })

  it.each(sources.map((s) => [s.file, s]))('%s only uses defined, semantic tokens', (_, { file, text }) => {
    const used = [...styleOf(text, file).matchAll(/var\((--[\w-]+)/g)].map((m) => m[1])
    expect(used.filter((t) => !defined.has(t)), 'unknown token').toEqual([])
    expect(used.filter((t) => palette.has(t)), 'palette token used directly — use a semantic --color-* token').toEqual([])
  })
})
