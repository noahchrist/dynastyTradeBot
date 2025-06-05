import { useLocation, useParams, useNavigate } from 'react-router-dom';

function LeaguePage() {
  const { leagueId } = useParams();
  const location = useLocation();
  const leagueData = location.state?.leagueData;
  const navigate = useNavigate();

  if (!leagueData) {
    return <div>Missing league data. Try returning to the home page.</div>;
  }

  return (
    <div style={{ padding: '2rem', textAlign: 'center' }}>
      <h1 style={{ fontSize: '2.5rem', fontWeight: 'bold', marginBottom: '2rem' }}>
        {leagueData.league_name} ({leagueData.season})
      </h1>

      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.5rem' }}>
        {leagueData.teams.map((team) => (
        <div
            key={team.team_id}
            onClick={() => navigate(`/league/${leagueId}/team/${team.team_id}`, { state: { leagueData } })}
            style={{
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            width: '90%',
            maxWidth: '600px',
            background: 'rgba(255,255,255,0.15)',
            padding: '1rem 1.5rem',
            borderRadius: '0.75rem',
            boxShadow: '0 2px 12px rgba(0,0,0,0.1)',
            transition: 'background 0.2s',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(255,255,255,0.25)')}
            onMouseLeave={(e) => (e.currentTarget.style.background = 'rgba(255,255,255,0.15)')}
        >
            <img
            src={`https://sleepercdn.com/avatars/${team.avatar || 'default.jpg'}`}
            alt="Team Avatar"
            style={{
                width: '80px',
                height: '80px',
                borderRadius: '50%',
                marginRight: '1.5rem',
                objectFit: 'cover',
                background: 'white',
            }}
            onError={(e) => {
                e.target.onerror = null;
                e.target.src = '/default-avatar.png';
            }}
            />
            <div style={{ textAlign: 'left' }}>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
                {team.team_name}
            </div>
            <div style={{ fontSize: '1rem', opacity: 0.8 }}>
                {team.owner_display_name}
            </div>
            </div>
        </div>
        ))}
      </div>
    </div>
  );
}

export default LeaguePage;
