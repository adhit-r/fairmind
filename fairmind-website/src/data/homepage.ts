export interface HeroSection {
  title: string;
  subtitle: string;
  description: string;
  ctaPrimary: {
    text: string;
    href: string;
  };
  ctaSecondary: {
    text: string;
    href: string;
  };
}

export interface Feature {
  title: string;
  description: string;
  icon: string;
  color: string;
  benefits: string[];
  link: {
    text: string;
    href: string;
  };
}

export interface AboutSection {
  title: string;
  description: string;
  ctaPrimary: {
    text: string;
    href: string;
  };
  ctaSecondary: {
    text: string;
    href: string;
  };
}

export interface CTASection {
  title: string;
  description: string;
  ctaPrimary: {
    text: string;
    href: string;
  };
  ctaSecondary: {
    text: string;
    href: string;
  };
}

export interface Stats {
  value: string;
  label: string;
}

export const heroData: HeroSection = {
  title: "AI Governance",
  subtitle: "Platform",
  description: "Open-source AI governance platform with advanced bias detection, model explainability, and compliance monitoring. Built with SHAP, LIME, and comprehensive fairness metrics for responsible AI development.",
  ctaPrimary: {
    text: "View Demo",
    href: "/demo"
  },
  ctaSecondary: {
    text: "Documentation",
    href: "/docs"
  }
};

export const featuresData: Feature[] = [
  {
    title: "Real-time Bias Monitoring",
    description: "Monitor model predictions for demographic bias with real-time alerts and automated bias scoring across protected groups.",
    icon: "search",
    color: "blue",
    benefits: [
      "Demographic parity difference",
      "Equal opportunity metrics", 
      "Disparate impact analysis"
    ],
    link: {
      text: "Explore bias monitoring",
      href: "/features#bias-monitoring"
    }
  },
  {
    title: "Model Explainability",
    description: "SHAP and LIME integration for model interpretability and decision transparency.",
    icon: "lightbulb",
    color: "purple",
    benefits: [
      "SHAP and LIME integration",
      "Interactive explanation dashboards",
      "Feature importance visualization"
    ],
    link: {
      text: "Learn about explainability",
      href: "/features#explainability"
    }
  },
  {
    title: "Model Simulation",
    description: "Comprehensive model testing and validation with synthetic data generation and performance analysis.",
    icon: "flask",
    color: "indigo",
    benefits: [
      "Synthetic data generation",
      "Performance analysis",
      "Risk assessment"
    ],
    link: {
      text: "Try simulation",
      href: "/demo"
    }
  }
];

export const aboutData: AboutSection = {
  title: "Empowering businesses with intelligent data solutions",
  description: "Fairmind is a leading provider of AI governance and bias detection solutions, helping organizations build trustworthy and ethical AI systems. Our platform combines cutting-edge technology with deep domain expertise to deliver actionable insights and ensure regulatory compliance. With a team of AI ethics experts and data scientists, we're committed to making AI more transparent, accountable, and fair for everyone.",
  ctaPrimary: {
    text: "Learn More",
    href: "/about"
  },
  ctaSecondary: {
    text: "Contact Us",
    href: "/contact"
  }
};

export const ctaData: CTASection = {
  title: "Ready to transform your data into insights?",
  description: "Open-source AI governance platform with advanced bias detection and model explainability capabilities.",
  ctaPrimary: {
    text: "View Demo",
    href: "/demo"
  },
  ctaSecondary: {
    text: "Documentation",
    href: "/docs"
  }
};

export const statsData: Stats[] = [
  {
    value: "22 Dashboards",
    label: "Specialized AI governance tools"
  },
  {
    value: "Open Source",
    label: "MIT License"
  },
  {
    value: "Neo4j + SHAP",
    label: "Knowledge Graph + Explainability"
  }
];
