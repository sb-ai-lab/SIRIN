import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"

export default defineConfig({
  base: "./",
  define: { "process.env.NODE_ENV": JSON.stringify("production") },
  plugins: [react()],
  build: {
    outDir: "build",
    assetsDir: "",
    // Emit fonts (and other assets) as hashed FILES instead of base64 data: URIs. Lib mode inlines
    // every asset by default, which re-shipped ~350KB of base64 Manrope/IBM Plex Mono in the CSS.
    assetsInlineLimit: 0,
    lib: {
      entry: "./src/index.tsx",
      formats: ["es"],
      fileName: "index-[hash]",
    },
    cssCodeSplit: false,
    rollupOptions: {
      output: {
        assetFileNames: (asset) =>
          asset.name?.endsWith(".css") ? "style-[hash][extname]" : "[name]-[hash][extname]",
      },
    },
  },
})
