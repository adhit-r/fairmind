const TopNav = () => {
  return (
    <header className="bg-gray-800 text-white p-4 flex justify-between items-center">
      <div className="text-lg font-bold">Home {'>'} AI Governance Dashboard</div>
      <div className="flex space-x-4">
        <input
          type="text"
          placeholder="Search Models and Assessments..."
          className="bg-gray-700 text-white p-2 rounded"
        />
        <button className="bg-blue-500 text-white px-4 py-2 rounded">New Simulation</button>
        <button className="bg-green-500 text-white px-4 py-2 rounded">Governance Review</button>
      </div>
    </header>
  );
};

export default TopNav;
