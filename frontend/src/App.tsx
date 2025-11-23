import React, { useEffect, useState } from "react";
import { fetchHealth } from "./api";

export default function App() {
  const [data, setData] = useState<any>(null);
  useEffect(() => { fetchHealth().then(setData).catch(console.error); }, []);
  return (
    <div>
      <h1>Academy Agent Repository</h1>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}
