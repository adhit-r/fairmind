export interface Framework {
  slug: string;
  name: string;
  shortName: string;
  region: string;
  type: string;
  title: string;
  description: string;
  summary: string;
  requirements: { ref: string; label: string; detail: string }[];
  evidence: string[];
  faqs: { q: string; a: string }[];
}

// Regulatory summaries for orientation only. Each page states that FairMind is not legal advice.
export const frameworks: Framework[] = [
  {
    slug: 'eu-ai-act',
    name: 'EU AI Act (Regulation (EU) 2024/1689)',
    shortName: 'EU AI Act',
    region: 'European Union',
    type: 'Binding regulation',
    title: 'EU AI Act compliance: bias, risk, and oversight evidence',
    description:
      'Map AI bias testing, risk management, logging, and human oversight evidence to EU AI Act obligations for high-risk AI systems with FairMind.',
    summary:
      'The EU AI Act is a risk-based regulation that entered into force on 1 August 2024. Prohibited practices and general-purpose AI obligations already apply. The 2026 Digital Omnibus moved high-risk obligations to December 2027 for Annex III systems and August 2028 for products covered by Annex I. Providers of high-risk systems must show how they manage risk, govern training data for bias, keep logs, and enable human oversight.',
    requirements: [
      { ref: 'Art. 9', label: 'Risk management system', detail: 'A continuous process to identify, evaluate, and mitigate risks across the lifecycle.' },
      { ref: 'Art. 10', label: 'Data and data governance', detail: 'Examine training, validation, and test data for possible biases and take measures to detect, prevent, and mitigate them.' },
      { ref: 'Art. 11', label: 'Technical documentation', detail: 'Documentation that demonstrates the system meets the requirements before it is placed on the market.' },
      { ref: 'Art. 12', label: 'Record-keeping', detail: 'Automatic logging that makes the system traceable over its lifetime.' },
      { ref: 'Art. 14', label: 'Human oversight', detail: 'Design that lets people understand, monitor, and override the system.' },
      { ref: 'Art. 15', label: 'Accuracy and robustness', detail: 'Declared accuracy levels and resilience to errors and manipulation.' },
    ],
    evidence: [
      'Bias evaluation runs with thresholds declared before the run, linked to the exact model version',
      'Findings that carry an owner, a remediation, and a retest that links back to the original failure',
      'Reviewer decisions on every evidence-to-article mapping, with rationale',
      'An exportable evidence index pinned to the regulation version, with open findings left visible',
    ],
    faqs: [
      {
        q: 'Does the EU AI Act require bias testing?',
        a: 'For high-risk AI systems, Article 10 requires providers to examine training, validation, and test data for possible biases that are likely to affect health and safety, negatively impact fundamental rights, or lead to prohibited discrimination, and to take measures to detect, prevent, and mitigate them.',
      },
      {
        q: 'Can FairMind make my AI system EU AI Act compliant?',
        a: 'No tool can. FairMind organises the technical evidence your team produces, links it to the relevant obligations, and records human review. Conformity is decided through your own assessment process and, where required, a notified body.',
      },
      {
        q: 'Who does the EU AI Act apply to?',
        a: 'It applies to providers and deployers of AI systems placed on the EU market or whose output is used in the EU, including organisations based outside the EU.',
      },
    ],
  },
  {
    slug: 'dpdp-act',
    name: 'Digital Personal Data Protection Act, 2023 (India)',
    shortName: 'DPDP Act',
    region: 'India',
    type: 'Binding law',
    title: 'DPDP Act compliance for AI systems in India',
    description:
      "Document how your AI systems process personal data under India's DPDP Act 2023: data accuracy, safeguards, impact assessments, and audit evidence.",
    summary:
      "India's Digital Personal Data Protection Act, 2023 governs how organisations process digital personal data. The DPDP Rules, 2025, notified in November 2025, bring most obligations into force on 13 May 2027. AI systems that make or support decisions about people sit squarely inside it: data used for those decisions must be accurate and complete, and Significant Data Fiduciaries face impact assessments and audits.",
    requirements: [
      { ref: 'Sec. 4–6', label: 'Lawful processing and consent', detail: 'Process personal data only for a lawful purpose, with consent or a recognised legitimate use.' },
      { ref: 'Sec. 8(3)', label: 'Accuracy for decisions', detail: 'Ensure completeness, accuracy, and consistency when personal data is used to make a decision that affects the Data Principal.' },
      { ref: 'Sec. 8(5)', label: 'Security safeguards', detail: 'Reasonable security safeguards to prevent personal data breaches.' },
      { ref: 'Sec. 10', label: 'Significant Data Fiduciaries', detail: 'Data Protection Impact Assessments, periodic audits, and a Data Protection Officer based in India.' },
      { ref: 'Rule 13(3)', label: 'Algorithmic due diligence', detail: 'Significant Data Fiduciaries must verify that technical measures, including algorithmic software, used to host, store, transmit, or share personal data are not likely to pose a risk to Data Principals’ rights.' },
    ],
    evidence: [
      'An inventory of AI systems that process personal data, with owner and purpose',
      'Data quality and bias evaluations tied to the decisions each system supports',
      'Impact assessment records with reviewer sign-off and open risks',
      'Audit-ready exports that show what was tested, what failed, and what was fixed',
    ],
    faqs: [
      {
        q: 'Does the DPDP Act apply to AI models?',
        a: 'Yes, whenever an AI system processes digital personal data of individuals in India. The Act does not single out AI, but its accuracy, purpose, and safeguard duties apply to any processing an AI system performs.',
      },
      {
        q: 'What are the penalties under the DPDP Act?',
        a: 'Once the relevant provisions commence on 13 May 2027, the Data Protection Board can impose penalties of up to 250 crore rupees for failing to take reasonable security safeguards. Other breaches carry lower caps.',
      },
      {
        q: 'How does FairMind help with DPDP compliance?',
        a: 'FairMind keeps the technical evidence for each AI system (evaluations, findings, remediation, and reviewer decisions) in one record you can hand to your DPO or auditor. It does not provide legal advice.',
      },
    ],
  },
  {
    slug: 'niti-aayog',
    name: 'NITI Aayog Responsible AI principles',
    shortName: 'NITI Aayog RAI',
    region: 'India',
    type: 'National guidance',
    title: 'NITI Aayog Responsible AI principles, put into practice',
    description:
      "Turn NITI Aayog's seven Responsible AI for All principles into tested, reviewed evidence for each AI system you run in India.",
    summary:
      "NITI Aayog's Responsible AI for All papers (2021) set out seven principles for AI in India and how to put them into operation. They're voluntary, but sector regulators and public buyers increasingly expect teams to show how each principle is met.",
    requirements: [
      { ref: 'P1', label: 'Safety and reliability', detail: 'Systems behave as intended and risks of harm are managed.' },
      { ref: 'P2', label: 'Equality', detail: 'People in similar circumstances are treated equally.' },
      { ref: 'P3', label: 'Inclusivity and non-discrimination', detail: 'Systems do not unfairly exclude or discriminate against groups.' },
      { ref: 'P4', label: 'Privacy and security', detail: 'Personal data is protected throughout the lifecycle.' },
      { ref: 'P5', label: 'Transparency', detail: 'Design and functioning can be explained and audited.' },
      { ref: 'P6', label: 'Accountability', detail: 'Clear ownership for decisions the system makes or supports.' },
      { ref: 'P7', label: 'Positive human values', detail: 'Systems reinforce rather than undermine human values.' },
    ],
    evidence: [
      'Bias and non-discrimination evaluations across groups relevant to Indian deployments',
      'Named owners and reviewer decisions for every finding',
      'Transparency records: model version, intended use, and known limitations',
      'A principle-by-principle evidence index with gaps left visible',
    ],
    faqs: [
      {
        q: 'Are the NITI Aayog Responsible AI principles mandatory?',
        a: 'No. They are national guidance, not law. Sector regulators such as the RBI draw on similar principles, so documenting against them prepares you for binding rules.',
      },
      {
        q: 'How do I show inclusivity and non-discrimination?',
        a: 'Run bias evaluations on the groups your system affects, set thresholds before the run, fix what fails, and retest. FairMind links each of those steps into one reviewable record.',
      },
    ],
  },
  {
    slug: 'nist-ai-rmf',
    name: 'NIST AI Risk Management Framework (AI RMF 1.0)',
    shortName: 'NIST AI RMF',
    region: 'United States',
    type: 'Voluntary framework',
    title: 'NIST AI RMF: map, measure, and manage AI bias with evidence',
    description:
      'Implement the NIST AI Risk Management Framework with traceable evidence for the Govern, Map, Measure, and Manage functions, including fairness and harmful bias.',
    summary:
      'The NIST AI RMF 1.0 (January 2023) is a voluntary framework organised into four functions: Govern, Map, Measure, and Manage. It treats "fair, with harmful bias managed" as one of the characteristics of trustworthy AI. A Generative AI Profile (NIST AI 600-1) extends it to generative systems.',
    requirements: [
      { ref: 'GOVERN', label: 'Govern', detail: 'Policies, roles, and accountability for AI risk across the organisation.' },
      { ref: 'MAP', label: 'Map', detail: 'Context, intended use, and impacts of each AI system.' },
      { ref: 'MEASURE', label: 'Measure', detail: 'Evaluate trustworthiness characteristics, including fairness and bias (MEASURE 2.11), and document results.' },
      { ref: 'MANAGE', label: 'Manage', detail: 'Prioritise, respond to, and monitor identified risks.' },
    ],
    evidence: [
      'System records covering context and intended use (MAP)',
      'Evaluation runs and artifacts for fairness, safety, and robustness (MEASURE)',
      'Findings, remediation, and retests with owners (MANAGE)',
      'Reviewer decisions and policy links (GOVERN)',
    ],
    faqs: [
      {
        q: 'Is the NIST AI RMF mandatory?',
        a: 'No. It is voluntary, but it is widely used as a reference by US agencies, enterprises, and procurement teams, and it maps well onto the EU AI Act and ISO/IEC 42001.',
      },
      {
        q: 'Where does bias testing fit in the NIST AI RMF?',
        a: 'Mainly in the Measure function. MEASURE 2.11 calls for fairness and bias to be evaluated and the results documented. The Manage function then covers responding to what you find.',
      },
    ],
  },
  {
    slug: 'iso-42001',
    name: 'ISO/IEC 42001:2023 AI management system',
    shortName: 'ISO/IEC 42001',
    region: 'International',
    type: 'Certifiable standard',
    title: 'ISO/IEC 42001 evidence for your AI management system',
    description:
      'Collect the operational evidence ISO/IEC 42001 auditors ask for: AI risk and impact assessments, data quality, monitoring, and corrective actions.',
    summary:
      'ISO/IEC 42001:2023 is the international standard for an AI management system (AIMS). It follows the familiar ISO management-system structure and can be certified by accredited bodies. Auditors look for evidence that risks and impacts are assessed and that controls actually operate.',
    requirements: [
      { ref: 'Cl. 6', label: 'Planning', detail: 'AI risk assessment, risk treatment, and AI system impact assessment.' },
      { ref: 'Cl. 8', label: 'Operation', detail: 'Operate the planned processes and keep evidence that they ran.' },
      { ref: 'Cl. 9', label: 'Performance evaluation', detail: 'Monitoring, measurement, internal audit, and management review.' },
      { ref: 'Cl. 10', label: 'Improvement', detail: 'Nonconformity, corrective action, and continual improvement.' },
      { ref: 'Annex A', label: 'Controls', detail: 'Reference controls covering data, lifecycle, impact assessment, and third parties.' },
    ],
    evidence: [
      'Impact and risk assessment records per AI system',
      'Evaluation evidence showing controls operated, not only that they exist',
      'Corrective actions linked to retests',
      'Exportable packages for internal and certification audits',
    ],
    faqs: [
      {
        q: 'Does FairMind certify ISO/IEC 42001?',
        a: 'No. Certification comes from an accredited certification body. FairMind helps you produce and organise the operating evidence that an audit reviews.',
      },
      {
        q: 'How does ISO/IEC 42001 relate to the EU AI Act?',
        a: 'They overlap heavily on risk management, data governance, and documentation. Evidence collected once can support both when a reviewer accepts the mapping.',
      },
    ],
  },
  {
    slug: 'rbi-free-ai',
    name: 'RBI FREE-AI framework',
    shortName: 'RBI FREE-AI',
    region: 'India',
    type: 'Committee report',
    title: 'RBI FREE-AI: responsible AI evidence for banks and NBFCs',
    description:
      "Prepare evidence for the Reserve Bank of India's FREE-AI framework: board-approved AI policy, model inventory, fairness testing, audits, and incident handling.",
    summary:
      "The Framework for Responsible and Ethical Enablement of AI (FREE-AI) is the report of a committee set up by the Reserve Bank of India, published in August 2025. It sets out seven guiding principles (Sutras) and 26 recommendations. They are advisory until the RBI issues directions, but they signal what lenders and other regulated entities will be expected to show: AI policies, inventories, fairness testing, and audits.",
    requirements: [
      { ref: 'Governance', label: 'Board-approved AI policy', detail: 'Clear accountability for AI use, approved at board level.' },
      { ref: 'Inventory', label: 'AI inventory', detail: 'An up-to-date record of AI models and use cases in production.' },
      { ref: 'Fairness', label: 'Fairness and equity', detail: 'AI must not produce unfair or discriminatory outcomes for customers.' },
      { ref: 'Assurance', label: 'Audits and monitoring', detail: 'Risk-based audits and ongoing monitoring of AI systems.' },
      { ref: 'Protection', label: 'Incidents and disclosure', detail: 'Incident reporting and customer-facing transparency for AI-driven decisions.' },
    ],
    evidence: [
      'An AI system register with owners, versions, and intended use',
      'Fairness evaluations for credit, pricing, and fraud models',
      'Findings and remediation history ready for internal audit',
      'Reviewer decisions that show human accountability',
    ],
    faqs: [
      {
        q: 'Who does RBI FREE-AI apply to?',
        a: 'Its recommendations are aimed at entities regulated by the Reserve Bank of India, such as banks, NBFCs, and payment system operators, that build or use AI. They are not binding until the RBI issues directions.',
      },
      {
        q: 'How do I test a credit scoring model for bias?',
        a: 'Compare outcomes and error rates across the customer groups the model affects, against thresholds you set before testing. Then record the fixes and retest. FairMind keeps that chain together for audit.',
      },
    ],
  },
  {
    slug: 'gdpr',
    name: 'General Data Protection Regulation (GDPR)',
    shortName: 'GDPR',
    region: 'European Union',
    type: 'Binding regulation',
    title: 'GDPR and AI: automated decisions, DPIAs, fairness evidence',
    description:
      'Document GDPR obligations for AI systems: fairness and accuracy principles, Article 22 automated decisions, and Data Protection Impact Assessments.',
    summary:
      'The GDPR applies to any AI system that processes personal data of people in the EU. Its fairness and accuracy principles, rules on solely automated decisions, and impact assessment duty all bear directly on how AI models are built and run.',
    requirements: [
      { ref: 'Art. 5', label: 'Fairness and accuracy', detail: 'Process personal data fairly and keep it accurate.' },
      { ref: 'Art. 22', label: 'Automated decisions', detail: 'Rights around decisions based solely on automated processing with legal or similarly significant effects.' },
      { ref: 'Art. 25', label: 'Data protection by design', detail: 'Build safeguards into systems from the start.' },
      { ref: 'Art. 35', label: 'Impact assessments', detail: 'A DPIA where processing is likely to pose a high risk to individuals.' },
    ],
    evidence: [
      'Fairness evaluations supporting DPIAs',
      'Human oversight records for decisions with significant effects',
      'Model version and data lineage for each system',
      'Exports your DPO can attach to a DPIA',
    ],
    faqs: [
      {
        q: 'Does GDPR ban automated decision-making?',
        a: 'Article 22 restricts decisions based solely on automated processing that have legal or similarly significant effects, unless an exception applies and safeguards such as human intervention are in place.',
      },
      {
        q: 'Is a DPIA required for AI?',
        a: 'Often. A DPIA is required when processing is likely to result in high risk, and supervisory authorities commonly list AI-driven profiling and evaluation of individuals as high risk.',
      },
    ],
  },
];
