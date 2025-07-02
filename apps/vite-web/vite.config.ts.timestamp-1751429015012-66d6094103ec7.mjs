// vite.config.ts
import { defineConfig } from "file:///Users/timdelisle/Dev/area-code/node_modules/.pnpm/vite@5.4.19_@types+node@24.0.4/node_modules/vite/dist/node/index.js";
import react from "file:///Users/timdelisle/Dev/area-code/node_modules/.pnpm/@vitejs+plugin-react@4.6.0_vite@5.4.19/node_modules/@vitejs/plugin-react/dist/index.mjs";
import { tanstackRouter } from "file:///Users/timdelisle/Dev/area-code/node_modules/.pnpm/@tanstack+router-plugin@1.121.41_@tanstack+react-router@1.121.41_vite@5.4.19/node_modules/@tanstack/router-plugin/dist/esm/vite.js";
import path from "path";
var __vite_injected_original_dirname = "/Users/timdelisle/Dev/area-code/apps/vite-web";
var vite_config_default = defineConfig({
  plugins: [react(), tanstackRouter()],
  css: {
    postcss: path.resolve(__vite_injected_original_dirname, "./postcss.config.js")
  },
  resolve: {
    alias: {
      "@": path.resolve(__vite_injected_original_dirname, "./src"),
      "@workspace/ui": path.resolve(__vite_injected_original_dirname, "../../packages/ui/src")
    }
  }
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcudHMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCIvVXNlcnMvdGltZGVsaXNsZS9EZXYvYXJlYS1jb2RlL2FwcHMvdml0ZS13ZWJcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfZmlsZW5hbWUgPSBcIi9Vc2Vycy90aW1kZWxpc2xlL0Rldi9hcmVhLWNvZGUvYXBwcy92aXRlLXdlYi92aXRlLmNvbmZpZy50c1wiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9pbXBvcnRfbWV0YV91cmwgPSBcImZpbGU6Ly8vVXNlcnMvdGltZGVsaXNsZS9EZXYvYXJlYS1jb2RlL2FwcHMvdml0ZS13ZWIvdml0ZS5jb25maWcudHNcIjtpbXBvcnQgeyBkZWZpbmVDb25maWcgfSBmcm9tIFwidml0ZVwiO1xuaW1wb3J0IHJlYWN0IGZyb20gXCJAdml0ZWpzL3BsdWdpbi1yZWFjdFwiO1xuaW1wb3J0IHsgdGFuc3RhY2tSb3V0ZXIgfSBmcm9tIFwiQHRhbnN0YWNrL3JvdXRlci1wbHVnaW4vdml0ZVwiO1xuaW1wb3J0IHBhdGggZnJvbSBcInBhdGhcIjtcblxuZXhwb3J0IGRlZmF1bHQgZGVmaW5lQ29uZmlnKHtcbiAgcGx1Z2luczogW3JlYWN0KCksIHRhbnN0YWNrUm91dGVyKCldLFxuICBjc3M6IHtcbiAgICBwb3N0Y3NzOiBwYXRoLnJlc29sdmUoX19kaXJuYW1lLCBcIi4vcG9zdGNzcy5jb25maWcuanNcIiksXG4gIH0sXG4gIHJlc29sdmU6IHtcbiAgICBhbGlhczoge1xuICAgICAgXCJAXCI6IHBhdGgucmVzb2x2ZShfX2Rpcm5hbWUsIFwiLi9zcmNcIiksXG4gICAgICBcIkB3b3Jrc3BhY2UvdWlcIjogcGF0aC5yZXNvbHZlKF9fZGlybmFtZSwgXCIuLi8uLi9wYWNrYWdlcy91aS9zcmNcIiksXG4gICAgfSxcbiAgfSxcbn0pO1xuIl0sCiAgIm1hcHBpbmdzIjogIjtBQUF5VCxTQUFTLG9CQUFvQjtBQUN0VixPQUFPLFdBQVc7QUFDbEIsU0FBUyxzQkFBc0I7QUFDL0IsT0FBTyxVQUFVO0FBSGpCLElBQU0sbUNBQW1DO0FBS3pDLElBQU8sc0JBQVEsYUFBYTtBQUFBLEVBQzFCLFNBQVMsQ0FBQyxNQUFNLEdBQUcsZUFBZSxDQUFDO0FBQUEsRUFDbkMsS0FBSztBQUFBLElBQ0gsU0FBUyxLQUFLLFFBQVEsa0NBQVcscUJBQXFCO0FBQUEsRUFDeEQ7QUFBQSxFQUNBLFNBQVM7QUFBQSxJQUNQLE9BQU87QUFBQSxNQUNMLEtBQUssS0FBSyxRQUFRLGtDQUFXLE9BQU87QUFBQSxNQUNwQyxpQkFBaUIsS0FBSyxRQUFRLGtDQUFXLHVCQUF1QjtBQUFBLElBQ2xFO0FBQUEsRUFDRjtBQUNGLENBQUM7IiwKICAibmFtZXMiOiBbXQp9Cg==
