import { defineConfig } from "fumadocs-ui/config";
import { FumadocsUI } from "fumadocs-ui/components";
import { MDX } from "fumadocs-mdx/components";

export default defineConfig({
  name: "Fairmind Documentation",
  baseUrl: "https://fairmind.xyz",
  theme: {
    colors: {
      primary: "hsl(var(--primary))",
    },
  },
  components: {
    page: {
      toc: true,
      lastModified: true,
    },
  },
  pages: [
    {
      title: "Getting Started",
      url: "/docs/getting-started",
      icon: "rocket",
    },
    {
      title: "User Guides",
      url: "/docs/user-guides",
      icon: "book",
    },
    {
      title: "API Reference",
      url: "/docs/api",
      icon: "code",
    },
    {
      title: "Developer Docs",
      url: "/docs/developer",
      icon: "wrench",
    },
    {
      title: "Tutorials",
      url: "/docs/tutorials",
      icon: "graduation-cap",
    },
    {
      title: "Examples",
      url: "/docs/examples",
      icon: "lightbulb",
    },
  ],
  sidebar: [
    {
      title: "Documentation",
      items: [
        {
          title: "Getting Started",
          url: "/docs/getting-started",
        },
        {
          title: "Installation",
          url: "/docs/installation",
        },
      ],
    },
    {
      title: "User Guides",
      items: [
        {
          title: "Bias Detection",
          url: "/docs/bias-detection",
        },
        {
          title: "Model Provenance",
          url: "/docs/model-provenance",
        },
        {
          title: "Security & Compliance",
          url: "/docs/security-compliance",
        },
        {
          title: "Monitoring & Analytics",
          url: "/docs/monitoring",
        },
        {
          title: "Explainability",
          url: "/docs/explainability",
        },
        {
          title: "Simulation & Testing",
          url: "/docs/simulation",
        },
      ],
    },
    {
      title: "API Reference",
      items: [
        {
          title: "REST API",
          url: "/docs/api/rest",
        },
        {
          title: "Python SDK",
          url: "/docs/api/python",
        },
        {
          title: "JavaScript SDK",
          url: "/docs/api/javascript",
        },
      ],
    },
    {
      title: "Developer Docs",
      items: [
        {
          title: "Architecture",
          url: "/docs/architecture",
        },
        {
          title: "Contributing",
          url: "/docs/contributing",
        },
      ],
    },
    {
      title: "Tutorials",
      items: [
        {
          title: "First Pipeline",
          url: "/docs/tutorials/first-pipeline",
        },
        {
          title: "Custom Rules",
          url: "/docs/tutorials/custom-rules",
        },
        {
          title: "Real-time Monitoring",
          url: "/docs/tutorials/monitoring",
        },
      ],
    },
    {
      title: "Examples",
      items: [
        {
          title: "Python Examples",
          url: "/docs/examples/python",
        },
        {
          title: "JavaScript Examples",
          url: "/docs/examples/javascript",
        },
      ],
    },
  ],
});
