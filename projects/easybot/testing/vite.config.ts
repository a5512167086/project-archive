import { defineConfig } from "vite";
import { resolve } from "path";

export default defineConfig({
  build: {
    outDir: "dist",
    minify: false,
    emptyOutDir: true,
    lib: {
      entry: resolve(__dirname, "src/tests/load-test.ts"),
      formats: ["es"],
      fileName: () => "load-test.js",
    },
    rollupOptions: {
      external: [/^(k6|https?\:\/\/)(\/.*)?/],
    },
  },
});
