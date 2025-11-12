import React from 'react';

const LoginPage = ({ onLoginSuccess }) => {
  const [username, setUsername] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [error, setError] = React.useState('');
  const [isLoading, setIsLoading] = React.useState(false);
  const passwordInputRef = React.useRef(null);
  const togglePasswordRef = React.useRef(null);

  React.useEffect(() => {
    // Route Guard: If user is already logged in, notify parent
    if (sessionStorage.getItem('accessToken')) {
      onLoginSuccess();
    }
  }, [onLoginSuccess]);

  const togglePasswordVisibility = () => {
    if (passwordInputRef.current) {
      const type = passwordInputRef.current.getAttribute('type') === 'password' ? 'text' : 'password';
      passwordInputRef.current.setAttribute('type', type);
      togglePasswordRef.current.classList.toggle('fa-eye-slash');
    }
  };

  const handleLogin = async (event) => {
    event.preventDefault();
    setError('');
    setIsLoading(true);

    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    try {
      const response = await fetch(`${window.API_BASE_URL}/auth/token`, {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        sessionStorage.setItem('accessToken', data.access_token);
        sessionStorage.setItem('tokenType', data.token_type);
        sessionStorage.setItem('user', JSON.stringify(data.user));
        onLoginSuccess(); // <-- causes onLoginSuccess to be called with no argument
      } else {
        setError('Invalid credentials. Please try again.');
      }
    } catch (error) {
      console.error('Login error:', error);
      setError('An error occurred. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ background: 'linear-gradient(135deg, #0B4D6B 0%, #2196F3 50%, #E6F3F8 100%)' }}>
      <div className="w-full max-w-6xl flex rounded-3xl overflow-hidden medical-card animate-fade-in">
        {/* Left Side - Medical Branding */}
        <div className="hidden lg:flex w-1/2 bg-gradient-to-br from-medical-blue via-medical-accent to-medical-blue text-white p-12 flex-col justify-center relative floating-elements">
          <div className="relative z-10">
            <div className="flex items-center mb-8">
              <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center mr-4">
                <i className="fas fa-stethoscope text-2xl text-white"></i>
              </div>
              <div>
                <h1 className="text-3xl font-bold font-primary">Medical Portal</h1>
                <p className="text-blue-100 font-secondary">Dr. Dhingra's Clinic Management</p>
              </div>
            </div>
            <div className="space-y-6">
              <h2 className="text-4xl font-bold font-primary leading-tight">
                Advanced Healthcare<br />
                <span className="text-blue-200">Management System</span>
              </h2>
              <p className="text-lg text-blue-100 font-secondary leading-relaxed">
                Secure access to patient records, appointment scheduling, and comprehensive clinic operations management.
              </p>
            </div>
            <div className="mt-12 grid grid-cols-2 gap-6">
              <div className="bg-white/10 p-4 rounded-xl">
                <div className="flex items-center mb-2">
                  <i className="fas fa-shield-alt text-blue-200 mr-3"></i>
                  <span className="font-semibold">Secure Access</span>
                </div>
                <p className="text-sm text-blue-100">HIPAA compliant security</p>
              </div>
              <div className="bg-white/10 p-4 rounded-xl">
                <div className="flex items-center mb-2">
                  <i className="fas fa-clock text-blue-200 mr-3"></i>
                  <span className="font-semibold">24/7 Access</span>
                </div>
                <p className="text-sm text-blue-100">Always available portal</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Side - Login Form */}
        <div className="w-full lg:w-1/2 p-8 lg:p-16 flex flex-col justify-center bg-white">
          <div className="w-full max-w-md mx-auto">
            <div className="lg:hidden flex items-center justify-center mb-8">
              <div className="w-12 h-12 bg-medical-accent rounded-xl flex items-center justify-center mr-3">
                <i className="fas fa-stethoscope text-white text-xl"></i>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-medical-dark font-primary">Medical Portal</h1>
                <p className="text-medical-gray font-secondary text-sm">Dr. Dhingra's Clinic</p>
              </div>
            </div>
            <div className="mb-8 animate-slide-up">
              <h2 className="text-3xl font-bold text-medical-dark font-primary mb-2">Welcome Back</h2>
              <p className="text-medical-gray font-secondary">Please sign in to access the medical dashboard</p>
            </div>

            <form onSubmit={handleLogin} className="space-y-6">
              <div className="input-group relative">
                <input
                  type="text"
                  id="username"
                  name="username"
                  placeholder=" "
                  className="w-full px-4 py-4 border-2 border-gray-200 rounded-xl focus:border-medical-accent focus:outline-none transition-all duration-300 font-secondary pr-12"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                />
                <label htmlFor="username" className="text-medical-gray font-secondary">Username</label>
              </div>

              <div className="input-group relative">
                <input
                  type="password"
                  id="password"
                  name="password"
                  placeholder=" "
                  className="w-full px-4 py-4 border-2 border-gray-200 rounded-xl focus:border-medical-accent focus:outline-none transition-all duration-300 font-secondary"
                  required
                  ref={passwordInputRef}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
                <label htmlFor="password" className="text-medical-gray font-secondary">Password</label>
                <i
                  className="fas fa-eye absolute top-1/2 right-4 -translate-y-1/2 cursor-pointer text-medical-gray"
                  id="togglePassword"
                  ref={togglePasswordRef}
                  onClick={togglePasswordVisibility}
                ></i>
              </div>

              <div className="flex items-center justify-between">
                <label className="flex items-center text-medical-gray font-secondary">
                  <input type="checkbox" className="w-4 h-4 text-medical-accent border-gray-300 rounded focus:ring-medical-accent mr-2" />
                  Remember me
                </label>
                <a href="#" className="text-medical-accent hover:text-medical-blue font-medium font-secondary transition-colors">
                  Forgot password?
                </a>
              </div>

              <button
                type="submit"
                className="w-full py-4 medical-button text-white font-semibold rounded-xl font-secondary tracking-wide relative z-10"
                disabled={isLoading}
              >
                {isLoading ? (
                  <span className="flex items-center justify-center">
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                    Signing In...
                  </span>
                ) : (
                  <span className="flex items-center justify-center">
                    <i className="fas fa-sign-in-alt mr-2"></i>
                    Sign In to Portal
                  </span>
                )}
              </button>

              {error && (
                <div id="error-message" className="bg-medical-error/10 border border-medical-error/20 text-medical-error px-4 py-3 rounded-xl font-secondary">
                  <div className="flex items-center">
                    <i className="fas fa-exclamation-triangle mr-2"></i>
                    <span>{error}</span>
                  </div>
                </div>
              )}
            </form>

            <div className="mt-8 pt-6 border-t border-gray-200">
              <div className="flex items-center justify-center space-x-4 text-sm text-medical-gray font-secondary">
                <span className="flex items-center">
                  <i className="fas fa-shield-alt text-medical-success mr-1"></i>
                  Secure Login
                </span>
                <span className="flex items-center">
                  <i className="fas fa-lock text-medical-success mr-1"></i>
                  Encrypted
                </span>
                <span className="flex items-center">
                  <i className="fas fa-user-md text-medical-success mr-1"></i>
                  HIPAA Compliant
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;