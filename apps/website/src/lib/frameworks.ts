import catalogue from '../../../backend/src/api/routers/pack_catalogue_data/catalogue.json';
import { registry } from './registry';

export interface Framework {
  slug: string;
  name: string;
  shortName: string;
  region: string;
  type: string;
  title: string;
  description: string;
  summary: string;
  sources?: { label: string; url: string }[];
  requirements: { ref: string; label: string; detail: string; controls?: string[] }[];
  evidence: string[];
  faqs: { q: string; a: string }[];
}

const controlNames = new Map(catalogue.commonControls.map((c) => [c.id, c.name]));

function mappedControls(keys: string[]): string[] {
  const ids = catalogue.crosswalk.filter((x) => keys.includes(x.key)).map((x) => x.commonControl);
  return [...new Set(ids)].map((id) => controlNames.get(id) ?? id).sort();
}

function copyFor(copy: Record<string, string>, id: string): string {
  if (!copy[id]) throw new Error(`frameworks.ts: no guide copy for catalogue requirement ${id}`);
  return copy[id];
}

// Requirement rows read from the catalogue, so IDs, titles and control mappings match the product.
// `copy` is FairMind's own one-line explanation per catalogue control, or per group when `byGroup` is set.
function catalogueRequirements(
  framework: string,
  copy: Record<string, string>,
  { refs = {}, byGroup = false }: { refs?: Record<string, string>; byGroup?: boolean } = {},
): Framework['requirements'] {
  const rows = catalogue.requirements.filter((r) => r.framework === framework && r.active !== false);
  if (!byGroup) {
    return rows.map((r) => ({
      ref: refs[r.control] ?? r.control,
      label: r.title,
      detail: copyFor(copy, r.control),
      controls: mappedControls([r.key]),
    }));
  }
  const groups = new Map<string, typeof rows>();
  for (const r of rows) groups.set(r.group, [...(groups.get(r.group) ?? []), r]);
  return [...groups].map(([group, rs]) => {
    const [ref, ...name] = group.split(' ');
    return {
      ref,
      label: name.join(' '),
      detail: `${rs.length} active requirements, ${rs[0].control} to ${rs[rs.length - 1].control}. ${copyFor(copy, ref)}`,
      controls: mappedControls(rs.map((r) => r.key)),
    };
  });
}

function stats(key: string) {
  const entry = registry.find((e) => e.key === key);
  if (!entry) throw new Error(`frameworks.ts: ${key} is not in the catalogue`);
  return entry;
}

const llm = stats('OWASPLLM');
const agentic = stats('OWASPAG');
const atlas = stats('ATLAS');
const aiuc = stats('AIUC1');
const nist600 = stats('NIST600');
const iso42005 = stats('ISO42005');
const mcp = stats('OWASPMCP');
const maestro = stats('MAESTRO');

// Regulatory summaries for orientation only. Each page states that FairMind is not legal advice.
export const frameworks: Framework[] = [
  {
    slug: 'owasp-agentic-top-10',
    name: 'OWASP Top 10 for Agentic Applications 2026',
    shortName: 'OWASP Agentic Top 10',
    region: 'International',
    type: 'Risk taxonomy',
    title: 'OWASP Top 10 for Agentic Applications: governance guide',
    description:
      'Govern AI agents against the OWASP Agentic Top 10 2026: goal hijack, tool misuse, privilege abuse and rogue agents, with evidence a person approves.',
    summary:
      'The OWASP Top 10 for Agentic Applications 2026 names the ten most critical security risks in AI agents that plan, call tools, keep memory and act across steps. The OWASP GenAI Security Project published it on 9 December 2025, with entries numbered ASI01 to ASI10. It extends the OWASP Top 10 for LLM Applications rather than replacing it: most agents are LLM applications too, so both lists apply.',
    sources: [
      {
        label: 'OWASP GenAI Security Project: Top 10 for Agentic Applications for 2026',
        url: 'https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/',
      },
    ],
    requirements: catalogueRequirements('OWASPAG', {
      ASI01: 'Content the agent reads, such as documents, emails or tool output, redirects its objective.',
      ASI02: 'The agent uses legitimate tools in unsafe ways or chains them beyond their intended purpose.',
      ASI03: 'Agents inherit, reuse or escalate credentials and permissions beyond what the task needs.',
      ASI04: 'Compromised tools, plugins, MCP servers, models or other agents enter the agent at build or run time.',
      ASI05: 'Code the agent writes or triggers runs without adequate isolation.',
      ASI06: 'Stored memory, retrieved context or embeddings are poisoned so later decisions go wrong.',
      ASI07: 'Messages between agents are spoofed, intercepted or tampered with.',
      ASI08: 'A fault in one agent or step spreads across connected agents and workflows.',
      ASI09: 'People over-trust confident agent output and approve harmful actions.',
      ASI10: 'Agents act outside their intended behaviour, persist, or evade oversight.',
    }),
    evidence: [
      `${agentic.evaluations} evaluations mapped to ASI01 to ASI10, each with a declared metric, threshold and evaluator status`,
      'Agent permission bounding and MCP server onboarding records, approved at the gate',
      'Agent registry and identity records, with an autonomy tier for each use case',
      'Kill-switch drills, runaway containment and incident records linked to the entries they address',
    ],
    faqs: [
      {
        q: 'How is the Agentic Top 10 different from the LLM Top 10?',
        a: 'The LLM Top 10 covers risks in applications that generate content. The Agentic Top 10 covers the risks that appear when a system plans, calls tools, keeps memory and acts across steps. An agent built on an LLM inherits both lists, so most teams map to both.',
      },
      {
        q: 'Is the OWASP Agentic Top 10 a compliance standard?',
        a: 'No. It is a voluntary risk taxonomy published under a Creative Commons licence. Teams use it to threat model agents and to show reviewers which agentic risks they test for. AIUC-1 covers similar ground as a certifiable standard with auditable requirements.',
      },
      {
        q: 'How does FairMind map the Agentic Top 10?',
        a: `The catalogue maps all ${agentic.requirements} entries to ${agentic.controls} common controls and ${agentic.workflows} workflows. One workflow run counts toward every ASI entry and every other framework requirement it covers, and a person approves the record at the gate before it is filed.`,
      },
    ],
  },
  {
    slug: 'aiuc-1',
    name: 'AIUC-1 AI agent standard',
    shortName: 'AIUC-1',
    region: 'International',
    type: 'Certifiable agent standard',
    title: 'AIUC-1 for AI agents: requirements and evidence',
    description:
      'Prepare AI agents for AIUC-1 certification: requirements across data and privacy, security, safety, reliability, accountability and society, mapped to evidence.',
    summary:
      'AIUC-1 is a certifiable standard for AI agents, maintained by the Artificial Intelligence Underwriting Company. Its requirements sit under six principles: data and privacy, security, safety, reliability, accountability, and society. It is updated every quarter, on 15 January, April, July and October, and the latest release is dated 15 October 2026. Certification runs through scoping, technical evaluations and an audit by an accredited auditor, is valid for one year, and includes quarterly retests against the version locked at scoping.',
    sources: [
      { label: 'AIUC-1', url: 'https://www.aiuc-1.com/' },
      { label: 'AIUC-1 changelog', url: 'https://standard.aiuc-1.com/changelog' },
    ],
    requirements: catalogueRequirements(
      'AIUC1',
      {
        A: 'Policies for input and output data, limits on what agents can access, and protection against leaks of personal data, IP and secrets.',
        B: 'Adversarial testing, input filtering, access control, and prevention of unauthorised agent actions.',
        C: 'A risk taxonomy, pre-deployment testing, and controls against harmful, out-of-scope and high-risk outputs.',
        D: 'Preventing hallucinated outputs and restricting unsafe tool calls, with recurring third-party testing.',
        E: 'Failure plans, named accountability, activity logs, vendor due diligence, disclosure and regulatory documentation.',
        F: 'Preventing cyber and catastrophic misuse of the AI system.',
      },
      { byGroup: true },
    ),
    evidence: [
      'Third-party testing records for each principle, scheduled every quarter',
      'Agent permission bounding and access review records for unauthorised-action requirements',
      'AI incident response plans and serious incident records for the failure-plan requirements',
      'Vendor and model due diligence, AI policies and change approvals with named owners',
    ],
    faqs: [
      {
        q: 'Can FairMind certify my agent against AIUC-1?',
        a: 'No. Certification comes from an accredited auditor through the AIUC-1 process. FairMind produces and organises the evidence that audit reviews, and records which person approved each piece.',
      },
      {
        q: 'Which AIUC-1 release does FairMind map?',
        a: `The 15 October 2026 release, with ${aiuc.requirements} active requirements. Retired requirements stay in the catalogue as history. Because AIUC-1 changes every quarter, confirm which release your certification is scoped to.`,
      },
      {
        q: 'How does AIUC-1 relate to the OWASP Agentic Top 10?',
        a: 'OWASP describes the risks; AIUC-1 turns agent risks into requirements an auditor can test. FairMind maps both to the same common controls, so one workflow run can count toward each.',
      },
    ],
  },
  {
    slug: 'owasp-mcp-top-10',
    name: 'OWASP MCP Top 10 (2025, beta)',
    shortName: 'OWASP MCP Top 10',
    region: 'International',
    type: 'Risk taxonomy',
    title: 'OWASP MCP Top 10: governing agent tools and MCP servers',
    description:
      'Govern the MCP servers your AI agents use against the OWASP MCP Top 10: token exposure, scope creep, tool poisoning, shadow servers and audit gaps.',
    summary:
      'The OWASP MCP Top 10 lists the most critical security risks in systems built on the Model Context Protocol, the open protocol that connects AI agents to tools and data. The project is in phase 3, beta release and pilot testing, with entries labelled MCP01:2025 to MCP10:2025, and OWASP expects the list to keep changing. Any agent that reaches tools through MCP servers carries these risks.',
    sources: [{ label: 'OWASP MCP Top 10 project', url: 'https://owasp.org/www-project-mcp-top-10/' }],
    requirements: catalogueRequirements('OWASPMCP', {
      MCP01: 'Hard-coded credentials, long-lived tokens, or secrets left in model memory and logs.',
      MCP02: 'Permissions granted to an MCP server or agent widen over time beyond what tasks need.',
      MCP03: 'Malicious instructions hidden in tool descriptions or metadata steer the agent.',
      MCP04: "Compromised MCP servers, packages or dependencies enter the agent's toolchain.",
      MCP05: 'Agent input reaches system commands or interpreters through MCP tools without validation.',
      MCP06: 'Instructions embedded in content an MCP tool returns take over the agent.',
      MCP07: 'MCP servers and clients that do not verify who is calling and what they may do.',
      MCP08: 'Missing logs and telemetry leave MCP tool calls untraceable during an incident.',
      MCP09: 'MCP servers deployed outside governance, unknown to the security team.',
      MCP10: 'Sensitive context shared with tools or models that should not see it.',
    }),
    evidence: [
      'MCP server and tool onboarding records, approved at the gate',
      `${mcp.evaluations} evaluations mapped to MCP01 to MCP10, including MCP server permission audit, shadow MCP servers and MCP authentication`,
      'Agent activity log monitoring that ties each tool call to an agent identity',
      'Periodic access reviews that catch scope creep',
    ],
    faqs: [
      {
        q: 'What is the Model Context Protocol?',
        a: 'An open protocol, introduced by Anthropic in November 2024, that standardises how AI applications connect to external tools and data sources. An MCP server exposes tools; an agent calls them. That makes MCP servers part of the attack surface of every agent that uses them.',
      },
      {
        q: 'Is the OWASP MCP Top 10 final?',
        a: 'No. It is a beta release in pilot testing, so names and order may change. FairMind maps the current IDs and records the version, so evidence stays traceable when the list changes.',
      },
      {
        q: 'How does FairMind map the MCP Top 10?',
        a: `The catalogue maps all ${mcp.requirements} entries to ${mcp.controls} common controls and ${mcp.workflows} workflows, centred on agent identity, access and permission bounding. Every workflow stops at a human approval gate before anything is recorded.`,
      },
    ],
  },
  {
    slug: 'csa-maestro',
    name: 'CSA MAESTRO agentic AI threat modelling framework',
    shortName: 'CSA MAESTRO',
    region: 'International',
    type: 'Threat modelling method',
    title: 'CSA MAESTRO: threat modelling for agentic AI',
    description:
      "Threat model AI agents with the Cloud Security Alliance's MAESTRO framework: seven layers from foundation models to the agent ecosystem, mapped to workflows.",
    summary:
      'MAESTRO (Multi-Agent Environment, Security, Threat, Risk, and Outcome) is a threat modelling framework for agentic AI, published by the Cloud Security Alliance on 6 February 2025 and written by Ken Huang. It breaks an agentic system into seven layers, from foundation models to the agent ecosystem, and looks for threats within each layer and across the boundaries between them.',
    sources: [
      {
        label: 'Cloud Security Alliance: Agentic AI Threat Modeling Framework: MAESTRO',
        url: 'https://cloudsecurityalliance.org/blog/2025/02/06/agentic-ai-threat-modeling-framework-maestro',
      },
    ],
    requirements: catalogueRequirements('MAESTRO', {
      L1: 'The core models agents run on, with threats such as adversarial inputs, model theft and backdoors.',
      L2: 'The data, stores and retrieval pipelines agents use, with threats such as poisoning and exfiltration.',
      L3: 'The frameworks used to build agents, with threats such as compromised components and input validation flaws.',
      L4: 'The infrastructure agents run on, with threats such as compromised containers and lateral movement.',
      L5: 'Monitoring and evaluation of agent behaviour, with threats such as manipulated metrics and evasion of detection.',
      L6: 'A vertical layer across all the others, covering security controls and regulatory compliance.',
      L7: 'Where agents meet users, tools and other agents, with threats such as impersonation and untrusted agents.',
    }),
    evidence: [
      'An agent threat model and taint trace per agent and multi-agent system',
      'Runtime guardrail reviews and red-teaming results linked to the layer they cover',
      'Inter-agent trust reviews for systems where agents call other agents',
      'Agent activity monitoring and evaluation records for the observability layer',
    ],
    faqs: [
      {
        q: 'What does MAESTRO add to existing threat models?',
        a: 'Layers specific to agentic systems and attention to threats that cross layers, such as a poisoned data store that changes what an agent does with its tools. It can be used alongside general methods your team already runs.',
      },
      {
        q: 'How does FairMind use MAESTRO?',
        a: `The catalogue maps all ${maestro.requirements} layers to ${maestro.controls} common controls and ${maestro.workflows} workflows. A person approves every threat model and finding at the gate before it is filed.`,
      },
    ],
  },
  {
    slug: 'owasp-llm-top-10',
    name: 'OWASP Top 10 for LLM Applications 2025',
    shortName: 'OWASP LLM Top 10',
    region: 'International',
    type: 'Risk taxonomy',
    title: 'OWASP Top 10 for LLM Applications: governance guide',
    description:
      'Map LLM apps and the agents built on them to the OWASP Top 10 for LLM Applications: prompt injection, excessive agency, data leakage and more.',
    summary:
      'The OWASP Top 10 for LLM Applications lists the most critical security risks in applications built on large language models, from prompt injection to unbounded consumption. Agents built on LLMs inherit every entry. FairMind maps the 2025 edition, numbered LLM01 to LLM10. The OWASP GenAI Security Project published a 2026 edition on 3 August 2026; re-mapping to it is pending, so evidence stays pinned to the 2025 IDs until then.',
    sources: [
      { label: 'OWASP Top 10 for LLM Applications 2025', url: 'https://genai.owasp.org/llm-top-10/' },
      { label: 'OWASP GenAI LLM Top 10 2026', url: 'https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/' },
    ],
    requirements: catalogueRequirements('OWASPLLM', {
      LLM01: "Inputs, typed or hidden in retrieved content, change the model's behaviour against its instructions.",
      LLM02: 'The application reveals personal data, credentials or confidential business data in its output.',
      LLM03: 'Third-party models, datasets, adapters or packages introduce vulnerabilities.',
      LLM04: 'Training, fine-tuning or embedding data is manipulated to plant backdoors, bias or errors.',
      LLM05: 'Model output reaches downstream systems without validation, opening injection and code execution paths.',
      LLM06: 'The model is given more functions, permissions or autonomy than the task needs.',
      LLM07: 'System prompts expose secrets or rules an attacker can use.',
      LLM08: 'Weaknesses in how vectors and embeddings are generated, stored or retrieved in RAG systems.',
      LLM09: 'The model produces false or misleading content that people or systems rely on.',
      LLM10: 'Uncontrolled inference use leads to denial of service, runaway cost or model extraction.',
    }),
    evidence: [
      `${llm.evaluations} evaluations mapped to LLM01 to LLM10, each with a declared metric, threshold and evaluator status`,
      'Runtime guardrail reviews and red-teaming results linked to the entries they cover',
      'AI-BOM and supply chain review records for models, datasets and packages',
      'Cost and consumption guardrails for unbounded consumption',
    ],
    faqs: [
      {
        q: 'Which edition of the LLM Top 10 does FairMind map?',
        a: 'The 2025 edition, LLM01 to LLM10. The 2026 edition renames and reorders entries. Until the catalogue is re-mapped, every record keeps the 2025 ID it was tested against.',
      },
      {
        q: 'Does the LLM Top 10 cover AI agents?',
        a: 'Partly. Excessive agency (LLM06) addresses agents directly, but risks such as goal hijack, memory poisoning and rogue agents sit in the OWASP Top 10 for Agentic Applications. FairMind maps both lists to the same common controls.',
      },
      {
        q: 'How does FairMind map the LLM Top 10?',
        a: `The catalogue maps all ${llm.requirements} entries to ${llm.controls} common controls and ${llm.workflows} workflows. Each evaluation names its metric and threshold, and every evaluator declares whether it is validated, runs through an external provider, reads metadata only, or is not yet available.`,
      },
    ],
  },
  {
    slug: 'mitre-atlas',
    name: 'MITRE ATLAS (Adversarial Threat Landscape for AI Systems)',
    shortName: 'MITRE ATLAS',
    region: 'International',
    type: 'Adversary technique catalogue',
    title: 'MITRE ATLAS: AI attack tactics mapped to governance',
    description:
      'Map AI agents and models to MITRE ATLAS tactics, from reconnaissance to impact, and link each tactic to evaluations and human-approved workflows.',
    summary:
      'MITRE ATLAS is a knowledge base of adversary tactics and techniques against AI systems, built on the structure of MITRE ATT&CK and drawn from real attacks and AI red-team demonstrations. It is updated monthly. The 2026.10 release, dated 28 October 2026, lists 16 tactics, 129 techniques and 92 sub-techniques, with 44 mitigations and 77 case studies. FairMind maps ATLAS at tactic level and covers 15 tactics; Lateral Movement, added in late 2025, is not mapped yet.',
    sources: [
      { label: 'MITRE ATLAS', url: 'https://atlas.mitre.org/' },
      { label: 'ATLAS data, release 2026.10', url: 'https://github.com/mitre-atlas/atlas-data' },
    ],
    requirements: catalogueRequirements(
      'ATLAS',
      {
        Reconnaissance: 'Gathering information about the target AI system, its models and its data.',
        'Resource Development': 'Acquiring or building the datasets, models, infrastructure and accounts an attack needs.',
        'Initial Access': 'Getting a foothold, for example through prompt injection or a compromised model supply chain.',
        'AI Model Access': 'Reaching the model through its API, the product that embeds it, or the model files.',
        Execution: "Running adversary-controlled code or commands, including through an agent's tools.",
        Persistence: 'Keeping access through poisoned data, backdoored models or altered agent memory.',
        'Privilege Escalation': "Gaining higher permissions, including by abusing an agent's access.",
        'Defense Evasion': 'Avoiding guardrails, classifiers and monitoring, for example through jailbreaks.',
        'Credential Access': 'Stealing credentials and secrets, including those placed in agent and tool context.',
        Discovery: "Learning about the AI system's configuration, system prompt, tools and environment.",
        Collection: 'Gathering data and AI artifacts of interest to the adversary.',
        'AI Attack Staging': 'Preparing the attack, such as crafting adversarial inputs or training proxy models. Named AI Attack Adaptation in the current matrix.',
        'Command and Control': 'Communicating with compromised systems, including through an AI agent.',
        Exfiltration: 'Moving data, model weights or other AI artifacts out of the environment.',
        Impact: 'Disrupting, degrading or manipulating the AI system or the decisions it supports.',
      },
      {
        refs: {
          'AI Model Access': 'AML.TA0000',
          'AI Attack Staging': 'AML.TA0001',
          Reconnaissance: 'AML.TA0002',
          'Resource Development': 'AML.TA0003',
          'Initial Access': 'AML.TA0004',
          Execution: 'AML.TA0005',
          Persistence: 'AML.TA0006',
          'Defense Evasion': 'AML.TA0007',
          Discovery: 'AML.TA0008',
          Collection: 'AML.TA0009',
          Exfiltration: 'AML.TA0010',
          Impact: 'AML.TA0011',
          'Privilege Escalation': 'AML.TA0012',
          'Credential Access': 'AML.TA0013',
          'Command and Control': 'AML.TA0014',
        },
      },
    ),
    evidence: [
      `${atlas.evaluations} evaluations mapped to ATLAS tactics, such as direct prompt injection for Initial Access and model extraction resistance for Exfiltration`,
      'Agent threat models with a taint trace of untrusted data flows',
      'AI red-teaming programme results linked to the tactic they exercise',
      'Vulnerability disclosure and patching records for findings',
    ],
    faqs: [
      {
        q: 'How does MITRE ATLAS relate to MITRE ATT&CK?',
        a: 'ATLAS follows the ATT&CK structure of tactics and techniques and adds the ones specific to AI systems, such as AI Model Access and adversarial input crafting. Tactics like Reconnaissance and Exfiltration share their names with ATT&CK, so security teams can read both side by side.',
      },
      {
        q: 'Why does FairMind map ATLAS at tactic level?',
        a: 'Techniques change with the monthly releases; tactics change rarely. Mapping evidence to tactics keeps it valid between releases. Each record still notes the ATLAS release it was reviewed against.',
      },
      {
        q: 'How does FairMind map ATLAS?',
        a: `The catalogue maps ${atlas.requirements} tactics to threat modelling, guardrails and vulnerability workflows (${atlas.workflows} in all). A person reviews each threat model and finding at the gate before it is filed.`,
      },
    ],
  },
  {
    slug: 'nist-ai-600-1',
    name: 'NIST AI 600-1, AI Risk Management Framework: Generative Artificial Intelligence Profile',
    shortName: 'NIST AI 600-1',
    region: 'United States',
    type: 'Voluntary framework',
    title: 'NIST AI 600-1 Generative AI Profile: the 12 risks, mapped',
    description:
      'Govern generative AI and LLM agents against the 12 risks in NIST AI 600-1, from confabulation to information security, with evidence for each.',
    summary:
      'NIST AI 600-1 is the Generative AI Profile of the NIST AI Risk Management Framework, published on 26 July 2024. It defines 12 risks that are novel to or made worse by generative AI, from CBRN information to value chain and component integration, and suggests actions to govern, map, measure and manage each one. For teams running LLM agents, it is the US reference for which generative risks to test and document.',
    sources: [
      {
        label: 'NIST AI 600-1',
        url: 'https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence',
      },
    ],
    requirements: catalogueRequirements('NIST600', {
      CBRN: 'Easier access to information or capabilities that could help create chemical, biological, radiological or nuclear weapons.',
      Confabulation: 'Confidently stated but false content, often called hallucination.',
      'Violent-Hateful': 'Easier production of violent, inciting, radicalising or hateful content.',
      'Data privacy': 'Leakage, unauthorised use or de-anonymisation of personal data.',
      Environmental: 'Energy use and emissions from training and running models.',
      'Harmful bias': 'Amplified historical and societal biases, and outputs that become uniform across users.',
      'Human-AI config': 'Over-reliance, automation bias and poorly designed handoffs between people and the system.',
      'Info integrity': 'Easier creation and spread of false, misleading or unverifiable content at scale.',
      'Info security': 'Lower barriers to offensive cyber operations, and new attack surfaces such as prompt injection and data poisoning.',
      IP: 'Easier reproduction of copyrighted or protected material, and exposure of trade secrets.',
      'Obscene-Abusive': 'Easier production of obscene, degrading or abusive content, including non-consensual imagery.',
      'Value chain': 'Third-party models, data and services integrated without transparency or traceability.',
    }),
    evidence: [
      `${nist600.evaluations} evaluations mapped to the 12 risks, each with a declared metric, threshold and evaluator status`,
      'AI risk assessments that record which of the 12 risks apply to each system and why',
      'Groundedness and hallucination controls for confabulation',
      'Foundation model intake and AI-BOM records for the value chain',
    ],
    faqs: [
      {
        q: 'How does NIST AI 600-1 relate to the AI RMF?',
        a: 'It is a profile: it applies AI RMF 1.0 to generative AI. Its suggested actions are organised under the same Govern, Map, Measure and Manage functions, so evidence for one supports the other.',
      },
      {
        q: 'Is NIST AI 600-1 mandatory?',
        a: 'No. It is voluntary guidance. US agencies, enterprises and buyers use it as a reference for what responsible generative AI practice looks like.',
      },
      {
        q: 'How does FairMind map NIST AI 600-1?',
        a: `The catalogue maps all ${nist600.requirements} risks to ${nist600.controls} common controls and ${nist600.workflows} workflows. Each workflow stops at a human approval gate before the record is filed.`,
      },
    ],
  },
  {
    slug: 'iso-42005',
    name: 'ISO/IEC 42005:2025 AI system impact assessment',
    shortName: 'ISO/IEC 42005',
    region: 'International',
    type: 'Guidance standard',
    title: 'ISO/IEC 42005 AI system impact assessment, in practice',
    description:
      'Run AI system impact assessments for agents and models the way ISO/IEC 42005:2025 describes, with reviewer sign-off and a record auditors can follow.',
    summary:
      'ISO/IEC 42005:2025 gives guidance for assessing how an AI system and its foreseeable applications can affect individuals and societies. Published on 28 May 2025 as a first edition, it covers how and when to assess, at which lifecycle stages, what the assessment record should contain, and how to fold the assessment into AI risk management and an AI management system. For AI agents, it is the method for working out what an agent could do to the people it reaches before it is deployed.',
    sources: [{ label: 'IEC Webstore: ISO/IEC 42005:2025', url: 'https://webstore.iec.ch/en/publication/107659' }],
    requirements: catalogueRequirements('ISO42005', {
      Method:
        'FairMind uses the standard as the method behind its impact assessment workflows rather than mapping it clause by clause, because the ISO text is licensed.',
    }),
    evidence: [
      'AI system impact assessments per system, with reviewer sign-off and open impacts left visible',
      'Workforce impact and consultation records',
      'Accessibility and inclusion reviews',
      'Links from each assessment to the ISO/IEC 42001 risk records it feeds',
    ],
    faqs: [
      {
        q: 'How does ISO/IEC 42005 relate to ISO/IEC 42001?',
        a: 'ISO/IEC 42001 requires an AI system impact assessment process (clause 6.1.4). ISO/IEC 42005 is guidance on how to carry one out. Teams working toward 42001 certification can use 42005 as the method for that process.',
      },
      {
        q: 'Is an ISO/IEC 42005 assessment a DPIA?',
        a: 'No. It can feed a GDPR Data Protection Impact Assessment or an EU AI Act fundamental rights impact assessment, but it does not replace either.',
      },
      {
        q: 'How does FairMind map ISO/IEC 42005?',
        a: `The catalogue treats the whole standard as the method for impact assessment and links it to ${iso42005.workflows} workflows. A person approves every assessment before it is filed.`,
      },
    ],
  },
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
