import resolve from '@rollup/plugin-node-resolve';
import typescript from '@rollup/plugin-typescript';
import terser from '@rollup/plugin-terser';
import json from '@rollup/plugin-json';

const outputDir = process.env.BUILD_DIR || 'dist';

export default {
  input: 'src/index.ts',
  output: {
    file: `${outputDir}/petkit-feeder-card.js`,
    format: 'esm',
    sourcemap: false,
  },
  plugins: [
    json(),
    resolve({
      extensions: ['.ts', '.js', '.json'],
    }),
    typescript({
      declaration: false,
      declarationMap: false,
      sourceMap: false,
      target: 'ES2022',
      module: 'ES2022',
      lib: ['ES2022', 'DOM', 'DOM.Iterable'],
    }),
    terser({
      format: {
        comments: false,
      },
      compress: {
        drop_console: false,
      },
    }),
  ],
};
