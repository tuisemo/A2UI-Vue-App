# A2UI Vue Demo

[中文版本](readme-zh.md)

## Project Overview

This project, `a2ui-vue-demo`, serves as a demonstration of integrating A2UI (Agent-to-User Interface) with Vue.js and Lit. Based on the A2UI Technical Report, it showcases how to build dynamic, agent-driven user interfaces by combining Vue 3's reactivity with Lit's efficient rendering capabilities. The core idea is to enable seamless communication between a backend agent and the frontend UI through the A2A protocol, allowing for real-time updates to the UI structure, data models, and components.

Key features include:
- **A2UI Bridge**: A layer for handling communication between Vue components and the A2UI processor.
- **Lit-based Rendering**: Utilizes Lit for rendering A2UI components within Vue applications.
- **Dynamic Surfaces**: Supports creating and updating UI surfaces based on agent messages.
- **Integration Modes**: Demonstrates Shadow DOM isolation, Light DOM integration, and communication bridging.

This demo is built on Vue 3, with dependencies like Pinia for state management and Tailwind CSS for styling. It provides a foundation for building AI-agent powered applications with modular, reusable UI components.

## Installation Instructions

To set up the project, follow these steps:

1. Clone the repository:
   ```
   git clone <repository-url>
   cd a2ui-lit-vue
   ```

2. Install dependencies using pnpm:
   ```
   pnpm install
   ```

   Note: This project uses pnpm as the package manager. If you don't have pnpm installed, you can install it via npm:
   ```
   npm install -g pnpm
   ```

## Running the Project

Once dependencies are installed, you can run the project using the following scripts defined in `package.json`:

- **Development Server**:
  ```
  pnpm dev
  ```
  This starts the Vite development server. Open `http://localhost:5173` (or the specified port) in your browser.

- **Build for Production**:
  ```
  pnpm build
  ```
  This compiles the project for production, outputting files to the `dist` directory.

- **Preview Production Build**:
  ```
  pnpm preview
  ```
  Serves the production build locally for testing.

- **Linting**:
  ```
  pnpm lint
  ```
  Runs ESLint on the source files to check for code quality issues.

## Dependencies

The project relies on the following main dependencies (from `package.json`):

### Runtime Dependencies
- `@microsoft/fetch-event-source`: ^2.0.1 (For handling server-sent events)
- `echarts`: ^5.5.0 (Charting library)
- `marked`: ^12.0.0 (Markdown parser)
- `pinia`: ^2.1.7 (State management for Vue)
- `vue`: ^3.4.21 (Vue.js framework)
- `zod`: ^3.23.0 (Schema validation)

### Development Dependencies
- `@vitejs/plugin-vue`: ^5.0.4 (Vite plugin for Vue)
- `autoprefixer`: ^10.4.19 (PostCSS plugin)
- `postcss`: ^8.4.38 (CSS processor)
- `tailwindcss`: ^3.4.3 (Utility-first CSS framework)
- `typescript`: ~5.4.0 (TypeScript support)
- `vite`: ^5.2.0 (Build tool)
- `vue-tsc`: ^2.0.6 (TypeScript compiler for Vue)

For a full list, refer to `package.json` and `pnpm-lock.yaml`.

## Project Structure

- `src/`: Source code directory
  - `components/`: Vue components
  - `composables/`: Reusable composition functions
  - `core/`: A2UI core logic (e.g., bridge, processor)
  - `stores/`: Pinia stores
  - `styles/`: CSS and Tailwind configurations
  - `types/`: TypeScript type definitions
- `server/`: Backend-related files (if applicable)
- `A2UI_Technical_Report.md`: Detailed technical documentation on A2UI integration.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes. Ensure your code follows the project's linting rules and includes relevant tests.

## License

This project is licensed under the MIT License. See the LICENSE file for details (if available).

For more in-depth technical details, refer to the [A2UI Technical Report](A2UI_Technical_Report.md).