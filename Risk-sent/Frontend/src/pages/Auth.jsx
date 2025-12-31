import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ShieldAlert, Mail, Lock, User, ArrowRight, Eye, EyeOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/hooks/useAuth';
import { useToast } from '@/hooks/use-toast';

export default function Auth() {
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: ''
  });

  const { signIn, signUp } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (isLogin) {
        const {user , error } = await signIn(formData.email, formData.password);
        if (error) throw error;
        if(user) {
        toast({ title: 'Welcome back!', description: 'Successfully signed in.' });
        navigate('/dashboard');
        }
      } else {
        const { error } = await signUp(formData.email, formData.password, formData.full_name);
        if (error) throw error;
        toast({ title: 'Account created!', description: 'You can now sign in.' });
        navigate('/dashboard');
      }
    } catch (error) {
      toast({ 
        title: 'Error', 
        description: error.message,
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex">
      {/* Left Panel - Form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md space-y-8">
          <div className="text-center">
            <Link to="/" className="inline-flex items-center gap-3 mb-8">
              <div className="bg-primary p-2 rounded-lg">
                <ShieldAlert className="text-primary-foreground" size={24} />
              </div>
              <span className="font-display font-bold text-foreground text-xl">
                RiskSense <span className="text-gradient">Pro</span>
              </span>
            </Link>
            <h1 className="font-display text-3xl font-bold text-foreground mb-2">
              {isLogin ? 'Welcome back' : 'Create account'}
            </h1>
            <p className="text-muted-foreground">
              {isLogin 
                ? 'Enter your credentials to access your dashboard' 
                : 'Start your free trial today'}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {!isLogin && (
              <div className="space-y-2">
                <Label htmlFor="full_name">Full Name</Label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
                  <Input
                    id="full_name"
                    type="text"
                    placeholder="John Doe"
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    className="pl-10"
                    required={!isLogin}
                  />
                </div>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
                <Input
                  id="email"
                  type="email"
                  placeholder="you@company.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="pl-10"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="pl-10 pr-10"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <Button 
              type="submit" 
              className="w-full bg-primary hover:bg-primary/90"
              disabled={loading}
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  {isLogin ? 'Sign In' : 'Create Account'}
                  <ArrowRight className="ml-2" size={18} />
                </>
              )}
            </Button>
          </form>

          <div className="text-center">
            <button
              onClick={() => setIsLogin(!isLogin)}
              className="text-muted-foreground hover:text-primary transition-colors"
            >
              {isLogin ? "Don't have an account? " : 'Already have an account? '}
              <span className="text-primary font-medium">
                {isLogin ? 'Sign up' : 'Sign in'}
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Right Panel - Decorative */}
      <div className="hidden lg:flex flex-1 bg-gradient-to-br from-primary/20 to-accent/10 items-center justify-center p-12 relative overflow-hidden">
        <div className="relative z-10 text-center max-w-lg">
          <div className="w-24 h-24 mx-auto mb-8 rounded-2xl bg-primary/20 flex items-center justify-center animate-float">
            <ShieldAlert className="text-primary" size={48} />
          </div>
          <h2 className="font-display text-3xl font-bold text-foreground mb-4">
            AI-Powered Risk Intelligence
          </h2>
          <p className="text-muted-foreground text-lg">
            Join thousands of financial professionals using RiskSense Pro to transform their risk analysis workflow.
          </p>
        </div>
        <div className="absolute inset-0 bg-gradient-to-t from-background to-transparent" />
        <div className="absolute top-1/4 -left-20 w-80 h-80 bg-primary/20 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 -right-20 w-80 h-80 bg-accent/20 rounded-full blur-3xl" />
      </div>
    </div>
  );
}
