const DashboardMetrics = () => {
  const metrics = [
    { title: "NIST Compliance", value: "82%", trend: "+3.2%" },
    { title: "Active Models", value: "47", trend: "+12" },
    { title: "Critical Risks", value: "3", trend: "-2" },
    { title: "LLM Safety Score", value: "88%", trend: "+5.1%" },
  ];

  return (
    <div className="grid grid-cols-4 gap-4">
      {metrics.map((metric, index) => (
        <div
          key={index}
          className="bg-gray-800 text-white p-4 rounded flex flex-col items-center"
        >
          <div className="text-lg font-bold">{metric.title}</div>
          <div className="text-2xl font-bold">{metric.value}</div>
          <div className="text-sm text-green-500">{metric.trend}</div>
        </div>
      ))}
    </div>
  );
};

export default DashboardMetrics;
