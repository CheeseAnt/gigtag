import { AuthProvider, AuthContext } from "react-oauth2-code-pkce"
import { useContext, useEffect } from "react"


const authConfig = {
  clientId: process.env.REACT_APP_CLIENT_ID,
  authorizationEndpoint: 'https://accounts.spotify.com/authorize',
  tokenEndpoint: 'https://accounts.spotify.com/api/token',
  redirectUri: process.env.REACT_APP_REDIRECT_URI ?? 'http://127.0.0.1:3000',
  scope: 'user-read-private user-read-email playlist-read-private playlist-read-collaborative user-library-read',
  onRefreshTokenExpire: (event) => event.logIn(undefined, undefined, "popup"),
}

const DebugInfo = () => {
    const {token} = useContext(AuthContext)
    const ctx = useContext(AuthContext)

    console.log('nothing here', ctx, ctx.loginInProgress);

    return <>
        <h4>Access Token</h4>
        <pre>{token}</pre>
    </>
}

const LogInButton = ({onSuccess}) => {
    const ctx = useContext(AuthContext)
    const isLoggedIn = !!ctx.token;

    useEffect(() => {
        if(isLoggedIn) {
            onSuccess(ctx.token);
        }
    }, [isLoggedIn, ctx.token, onSuccess]);

    return <button style={{
        backgroundColor: '#1DB954',
        alignItems: 'center',
        border: 'none',
        borderRadius: '.2rem',
        color: '#fff',
        cursor: 'pointer',
        display: 'flex',
        fontFamily: 'Rubik,Arial,Helvetica,sans-serif',
        justifyContent: 'center',
        minHeight: '32px',
        padding: '.25rem .5rem',
        transitionDuration: '.3s',
        transitionProperty: 'background-color,box-shadow',
    }}
    onClick={() => ctx.logIn()} disabled={ctx.loginInProgress || isLoggedIn}>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 496 512" style={{
            padding: "0.25rem 0.5rem",
            height: "1.5rem",
            fill: "#fff",
            width: "2em"
        }}><path d="M248 8C111.1 8 0 119.1 0 256s111.1 248 248 248 248-111.1 248-248S384.9 8 248 8zm100.7 364.9c-4.2 0-6.8-1.3-10.7-3.6-62.4-37.6-135-39.2-206.7-24.5-3.9 1-9 2.6-11.9 2.6-9.7 0-15.8-7.7-15.8-15.8 0-10.3 6.1-15.2 13.6-16.8 81.9-18.1 165.6-16.5 237 26.2 6.1 3.9 9.7 7.4 9.7 16.5s-7.1 15.4-15.2 15.4zm26.9-65.6c-5.2 0-8.7-2.3-12.3-4.2-62.5-37-155.7-51.9-238.6-29.4-4.8 1.3-7.4 2.6-11.9 2.6-10.7 0-19.4-8.7-19.4-19.4s5.2-17.8 15.5-20.7c27.8-7.8 56.2-13.6 97.8-13.6 64.9 0 127.6 16.1 177 45.5 8.1 4.8 11.3 11 11.3 19.7-.1 10.8-8.5 19.5-19.4 19.5zm31-76.2c-5.2 0-8.4-1.3-12.9-3.9-71.2-42.5-198.5-52.7-280.9-29.7-3.6 1-8.1 2.6-12.9 2.6-13.2 0-23.3-10.3-23.3-23.6 0-13.6 8.4-21.3 17.4-23.9 35.2-10.3 74.6-15.2 117.5-15.2 73 0 149.5 15.2 205.4 47.8 7.8 4.5 12.9 10.7 12.9 22.6 0 13.6-11 23.3-23.2 23.3z"></path></svg>
        {ctx.loginInProgress ? "Loading..." : "Continue With Spotify"}
    </button>
}

const SpotifyAuth = ({onAccessToken}) => {
    
    return <AuthProvider authConfig={authConfig}>
            {/* <DebugInfo /> */}
            <LogInButton onSuccess={onAccessToken} />
        </AuthProvider>
}

export { SpotifyAuth };
