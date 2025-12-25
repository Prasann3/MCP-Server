import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldAlert, ArrowRight, Brain, FileSearch, Lock, Zap, BarChart3, Shield } from 'lucide-react';
import { Button } from '@/components/ui/button';

const features = [
  {
    icon: Brain,
    title: 'AI-Powered Analysis',
    description: 'Advanced machine learning models analyze financial documents in real-time for comprehensive risk assessment.'
  },
  {
    icon: FileSearch,
    title: 'Document Intelligence',
    description: 'Upload 10-K reports, financial statements, and contracts for instant risk extraction and analysis.'
  },
  {
    icon: Lock,
    title: 'Enterprise Security',
    description: 'Bank-grade encryption and compliance with SOC 2, GDPR, and industry regulations.'
  },
  {
    icon: Zap,
    title: 'Real-time Insights',
    description: 'Get instant answers about financial risks with our streaming AI chat interface.'
  },
  {
    icon: BarChart3,
    title: 'Risk Quantification',
    description: 'Transform qualitative risk factors into actionable quantitative metrics.'
  },
  {
    icon: Shield,
    title: 'Compliance Ready',
    description: 'Built-in frameworks for regulatory compliance and audit trail documentation.'
  }
];

export default function Landing() {
  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-primary p-2 rounded-lg shadow-lg animate-pulse-glow">
              <ShieldAlert className="text-primary-foreground" size={24} />
            </div>
            <span className="font-display font-bold text-foreground text-xl tracking-tight">
              RiskSense <span className="text-gradient">Pro</span>
            </span>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/auth">
              <Button variant="ghost" className="text-muted-foreground hover:text-foreground">
                Sign In
              </Button>
            </Link>
            <Link to="/auth">
              <Button className="bg-primary hover:bg-primary/90">
                Get Started <ArrowRight className="ml-2" size={16} />
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="container mx-auto text-center max-w-4xl">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 mb-8">
            <Zap size={14} className="text-primary" />
            <span className="text-sm text-primary font-medium">AI-Powered Financial Risk Intelligence</span>
          </div>
          
          <h1 className="font-display text-5xl md:text-7xl font-bold text-foreground mb-6 leading-tight">
            Transform Risk Analysis with{' '}
            <span className="text-gradient">Intelligent AI</span>
          </h1>
          
          <p className="text-xl text-muted-foreground mb-10 max-w-2xl mx-auto leading-relaxed">
            Upload financial documents, ask questions in natural language, and receive instant, comprehensive risk assessments powered by advanced AI.
          </p>
          
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/auth">
              <Button size="lg" className="bg-primary hover:bg-primary/90 text-lg px-8 py-6 animate-pulse-glow">
                Start Free Trial <ArrowRight className="ml-2" size={20} />
              </Button>
            </Link>
            <Button size="lg" variant="outline" className="text-lg px-8 py-6 border-border hover:bg-secondary">
              Watch Demo
            </Button>
          </div>
        </div>

        {/* Floating Elements */}
        <div className="absolute top-1/4 left-10 w-72 h-72 bg-primary/10 rounded-full blur-3xl animate-float" />
        <div className="absolute bottom-1/4 right-10 w-96 h-96 bg-accent/10 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s' }} />
      </section>

      {/* Features Section */}
      <section className="py-20 px-6 relative">
        <div className="container mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-display text-4xl font-bold text-foreground mb-4">
              Enterprise-Grade Features
            </h2>
            <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
              Everything you need to analyze, quantify, and manage financial risks at scale.
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div 
                key={index}
                className="group p-8 rounded-2xl bg-card border border-border hover:border-primary/50 transition-all duration-300 hover:shadow-lg hover:shadow-primary/5"
              >
                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-6 group-hover:bg-primary/20 transition-colors">
                  <feature.icon className="text-primary" size={24} />
                </div>
                <h3 className="font-display text-xl font-semibold text-foreground mb-3">
                  {feature.title}
                </h3>
                <p className="text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6">
        <div className="container mx-auto">
          <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-primary/20 to-accent/10 border border-primary/20 p-12 md:p-16 text-center">
            <div className="relative z-10">
              <h2 className="font-display text-4xl md:text-5xl font-bold text-foreground mb-6">
                Ready to Transform Your Risk Analysis?
              </h2>
              <p className="text-muted-foreground text-lg mb-8 max-w-2xl mx-auto">
                Join leading financial institutions using RiskSense Pro to make smarter, faster decisions.
              </p>
              <Link to="/auth">
                <Button size="lg" className="bg-primary hover:bg-primary/90 text-lg px-8 py-6">
                  Get Started Free <ArrowRight className="ml-2" size={20} />
                </Button>
              </Link>
            </div>
            <div className="absolute inset-0 bg-gradient-to-t from-background/80 to-transparent" />
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-border">
        <div className="container mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <ShieldAlert className="text-primary" size={20} />
            <span className="font-display font-semibold text-foreground">RiskSense Pro</span>
          </div>
          <p className="text-muted-foreground text-sm">
            © 2024 RiskSense Pro. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
