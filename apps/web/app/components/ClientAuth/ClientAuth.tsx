
'use client';

import { Auth } from '@supabase/auth-ui-react';
import { ThemeSupa } from '@supabase/auth-ui-shared';
import { supabaseBrowser } from '@/lib/supabase';
import './ClientAuth.css';

export default function ClientAuth() {
  return (
    <div className="auth-container">
      <h1 className="auth-title">Codeless AI Builder</h1>
      <div className="auth-form-container">
        <div className="auth-card">
          <Auth
            supabaseClient={supabaseBrowser}
            appearance={{ theme: ThemeSupa }}
            theme="dark"
            providers={[]}
            redirectTo="http://localhost:3000"
          />
        </div>
      </div>
    </div>
  );
}