import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ScrollToTop from './components/ScrollToTop'; // Adjust path as needed
import Home from './pages/Home';
import LeaguePage from './pages/LeaguePage';
import TeamPage from './pages/TeamPage';

function App() {
  return (
    <Router>
      <ScrollToTop />
      <div style={{ padding: '2rem' }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/league/:leagueId" element={<LeaguePage />} />
          <Route path="/league/:leagueId/team/:teamId" element={<TeamPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
