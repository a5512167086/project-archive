import CustomMap from "./components/CustomMap";
import { customMapConfig } from "./config/common";

function App() {
  return (
    <div className="App">
      <CustomMap customMapConfig={customMapConfig} />
    </div>
  );
}

export default App;
