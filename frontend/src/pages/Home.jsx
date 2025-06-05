import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

function Home() {
  const [leagueId, setLeagueId] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!leagueId.trim()) return;

    try {
      const res = await fetch('http://localhost:8000/sleeper/league', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ league_id: leagueId.trim() }),
      });

      if (!res.ok) {
        throw new Error('Invalid league or unsupported format.');
      }

      const data = await res.json();
      navigate(`/league/${leagueId}`, { state: { leagueData: data } });
    } catch (err) {
      alert(err.message || 'Error fetching league info');
    }
  };

  return (
    <div
      style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
      }}
    >
      <h1
        style={{
          marginTop: '5rem',
          textAlign: 'center',
          fontSize: '3rem',
          fontWeight: 'bold',
          letterSpacing: '1px',
        }}
      >
        dynastyTradeBot 🧠🏈
      </h1>

      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          marginTop: '4rem',
        }}
      >
        <form
          onSubmit={handleSubmit}
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            fontSize: '1.5rem',
            gap: '1rem',
          }}
        >
          <label htmlFor="leagueId">Enter Sleeper League ID: 1181664632808194048</label>
          <input
            type="text"
            id="leagueId"
            value={leagueId}
            onChange={(e) => setLeagueId(e.target.value)}
            style={{
              fontSize: '1.2rem',
              padding: '0.5rem 1rem',
              borderRadius: '0.5rem',
              border: 'none',
              outline: 'none',
              width: '16rem',
              background: 'rgba(255, 255, 255, 0.2)',
              color: 'white',
            }}
          />
          <button
            type="submit"
            style={{
              fontSize: '1.2rem',
              padding: '0.5rem 2rem',
              borderRadius: '0.5rem',
              border: 'none',
              background: '#4e944f',
              color: 'white',
              cursor: 'pointer',
              fontWeight: 'bold',
            }}
          >
            Submit
          </button>
        </form>
      </div>
    </div>
  );
}

export default Home;
