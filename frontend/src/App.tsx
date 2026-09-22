import { Routes, Route } from 'react-router-dom';
import { ScanProvider } from './context/ScanContext';
import { AppLayout } from './components/layout/AppLayout';
import Home from './pages/Home';
import ResultsPage from './pages/ResultsPage';
import FindingsPage from './pages/FindingsPage';
import QuantumPage from './pages/QuantumPage';
import MigrationPage from './pages/MigrationPage';
import { InventoryPage } from './pages/InventoryPage';
import DiagnosticsPage from './pages/DiagnosticsPage';

function App() {
  return (
    <ScanProvider>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/results" element={<ResultsPage />} />
          <Route path="/findings" element={<FindingsPage />} />
          <Route path="/quantum" element={<QuantumPage />} />
          <Route path="/migration" element={<MigrationPage />} />
          <Route path="/enterprise-inventory" element={<InventoryPage />} />
          <Route path="/diagnostics" element={<DiagnosticsPage />} />
        </Routes>
      </AppLayout>
    </ScanProvider>
  );
}

export default App;
