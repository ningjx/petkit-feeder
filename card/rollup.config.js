import resolve from '@rollup/plugin-node-resolve';
import typescript from '@rollup/plugin-typescript';
import terser from '@rollup/plugin-terser';

export default {
  input: 'src/petkit-feeder-card.ts',
  output: {
    file: 'dist/petkit-feeder-card.js',
    format: 'esm',
    sourcemap: false,
  },
  plugins: [
    resolve({
      extensions: ['.ts', '.js'],
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
        drop_console: false, // 保留 console 用于调试
      },
    }),
  ],
};
