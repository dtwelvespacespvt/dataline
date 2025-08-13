import React from 'react';
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google';
import { useGoogleLogin } from '@/hooks/auth';

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || "YOUR_GOOGLE_CLIENT_ID";

interface GoogleAuthProps {
  onSuccess?: () => void;
  onError?: () => void;
}

export const GoogleAuth: React.FC<GoogleAuthProps> = ({ onSuccess, onError }) => {
  const { mutate: googleLogin } = useGoogleLogin();

  const handleLoginSuccess = (credentialResponse: any) => {
    googleLogin(
      { credential: credentialResponse.credential },
      {
        onSuccess: () => {
          console.log("Google login successful!");
          onSuccess?.();
        },
        onError: (error: any) => {
          console.error("Google login failed:", error);
          onError?.();
        },
      }
    );
  };

  const handleLoginError = () => {
    console.log("Google Login Failed");
    onError?.();
  };

  if (!GOOGLE_CLIENT_ID || GOOGLE_CLIENT_ID === "YOUR_GOOGLE_CLIENT_ID") {
    return null;
  }

  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <div className="mt-4">
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-600" />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="bg-gray-900 px-2 text-gray-400">Or continue with</span>
          </div>
        </div>
        <div className="mt-4">
          <GoogleLogin
            onSuccess={handleLoginSuccess}
            onError={handleLoginError}
            theme="filled_black"
            size="large"
            width="100%"
          />
        </div>
      </div>
    </GoogleOAuthProvider>
  );
};

export default GoogleAuth;
