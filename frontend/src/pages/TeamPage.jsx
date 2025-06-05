import { useParams, useLocation } from 'react-router-dom';
import { useEffect, useState } from 'react';
import axios from 'axios';

function TeamPage() {
  const { teamId } = useParams();
  const location = useLocation();
  const leagueData = location.state?.leagueData;
  const [assets, setAssets] = useState([]);
  const [rankings, setRankings] = useState(null);
  const [tradeSuggestions, setTradeSuggestions] = useState(null);

  if (!leagueData) {
    return <div style={{ textAlign: 'center' }}>Missing league data. Return to the home page.</div>;
  }

  const team = leagueData.teams.find((t) => String(t.team_id) === teamId);
  if (!team) {
    return <div style={{ textAlign: 'center' }}>Team not found.</div>;
  }

  useEffect(() => {
    axios.post('http://localhost:8000/players/info', {
      league_id: leagueData.league_id,
      team_id: parseInt(teamId)
    })
    .then((res) => {
      setAssets(res.data.players);  // Already sorted by value
    })
    .catch((err) => {
      console.error("Failed to fetch player info:", err);
    });

    axios.post('http://localhost:8000/league-rankings', {
      league_id: leagueData.league_id,
      team_id: parseInt(teamId)
    })
    .then((res) => {
      setRankings(res.data);
    })
    .catch((err) => {
      console.error("Failed to fetch league rankings:", err);
    });

  }, [teamId, leagueData]);

  // Group assets by position
  const grouped = {
    QB: [],
    RB: [],
    WR: [],
    TE: [],
    PICK: [],
  };

  assets.forEach((a) => {
    const pos = a.position;
    if (grouped[pos]) {
      grouped[pos].push(a);
    }
  });

  const renderGroup = (label, group) => (
    <>
      <h4 style={{ margin: '1rem 0 0.5rem' }}>{label}</h4>
      <ul style={{ paddingLeft: '1rem', margin: 0 }}>
        {group.map((a, index) => (
          <li key={a.player_id || `${a.name}-${index}`} style={{ marginBottom: '0.3rem' }}>
            {a.name} {a.position !== "PICK" ? `- ${a.position}, ${a.team}` : ""} - {a.value}
          </li>
        ))}
      </ul>
    </>
  );

  return (
    <div style={{ padding: '2rem' }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '1.5rem',
          marginBottom: '2rem',
          justifyContent: 'center',
        }}
      >
        <img
          src={`https://sleepercdn.com/avatars/${team.avatar || 'default.jpg'}`}
          alt="Team Avatar"
          style={{
            width: '100px',
            height: '100px',
            borderRadius: '50%',
            objectFit: 'cover',
            background: 'white',
          }}
          onError={(e) => {
            e.target.onerror = null;
            e.target.src = '/default-avatar.png';
          }}
        />
        <h1 style={{ fontSize: '2.5rem', fontWeight: 'bold', margin: 0 }}>
          {team.team_name}
        </h1>
      </div>

      {/* Layout: Left (Roster), Center (Button), Right (Rankings) */}
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        {/* Left Panel - Roster */}
        <div style={{ width: '30%', paddingRight: '1rem' }}>
          <h3 style={{ textAlign: 'center' }}>Current Roster</h3>
          {renderGroup("Quarterbacks", grouped.QB)}
          {renderGroup("Running Backs", grouped.RB)}
          {renderGroup("Wide Receivers", grouped.WR)}
          {renderGroup("Tight Ends", grouped.TE)}
          {renderGroup("Picks", grouped.PICK)}
        </div>

        {/* Center - Trade Generator Button + Output */}
        <div
          style={{
            width: '35%',
            textAlign: 'center',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            wordBreak: 'break-word', // Ensures long words wrap
            overflowWrap: 'break-word', // Ensures long words wrap
          }}
        >
          <button
            onClick={() => {
              axios.post('http://localhost:8000/generate-trade', {
                league_id: leagueData.league_id,
                team_id: parseInt(teamId)
              })
              .then((res) => {
                setTradeSuggestions(res.data);
              })
              .catch((err) => {
                console.error("Failed to generate trade:", err);
                setTradeSuggestions({ error: "Failed to fetch trade suggestions." });
              });
            }}
            style={{
              fontSize: '1.1rem',
              padding: '0.75rem 1.5rem',
              cursor: 'pointer',
              marginTop: '10rem'
            }}
          >
            Generate Trades with dynastyTradeBot™
          </button>

          {tradeSuggestions && (
            <pre
              style={{
                textAlign: 'left',
                marginTop: '2rem',
                fontSize: '0.9rem',
                maxWidth: '100%',
                width: '100%',
                overflowX: 'auto',
                whiteSpace: 'pre-wrap', // Wraps long lines
                wordBreak: 'break-word', // Breaks long words
                background: '#222',
                color: '#fff',
                borderRadius: '0.5rem',
                padding: '1rem',
                boxSizing: 'border-box'
              }}
            >
              {JSON.stringify(tradeSuggestions, null, 2)}
            </pre>
          )}
        </div>


        {/* Right Panel - League Rankings */}
        <div style={{ width: '30%', paddingLeft: '1rem' }}>
          <h3 style={{ textAlign: 'center' }}>League Rankings</h3>
          {rankings ? (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {Object.entries(rankings).map(([pos, data]) => (
                <li key={pos} style={{ marginBottom: '0.5rem', textAlign: 'center' }}>
                  <strong>{pos}</strong>: {data.rank ? `${data.rank} / ${data.total_teams}` : `No ${pos}s`}
                </li>
              ))}
            </ul>
          ) : (
            <p style={{ textAlign: 'center', fontStyle: 'italic' }}>Loading...</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default TeamPage;
