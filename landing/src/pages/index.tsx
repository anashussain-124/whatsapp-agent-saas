'use client';

import { useState } from 'react';
import Head from 'next/head';
import {
  MessageCircle,
  Calendar,
  Clock,
  IndianRupee,
  Bot,
  BarChart3,
  Shield,
  Zap,
  Users,
  CheckCircle2,
  ArrowRight,
  Star,
  Menu,
  X,
} from 'lucide-react';

// ─── Navigation ─────────────────────────────────────────────────────

function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-lg border-b border-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 bg-whatsapp rounded-xl flex items-center justify-center">
              <MessageCircle className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-gray-900">WhatsApp Agent</span>
          </div>

          <div className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-sm font-medium text-gray-600 hover:text-gray-900">Features</a>
            <a href="#how-it-works" className="text-sm font-medium text-gray-600 hover:text-gray-900">How It Works</a>
            <a href="#pricing" className="text-sm font-medium text-gray-600 hover:text-gray-900">Pricing</a>
            <a href="#testimonials" className="text-sm font-medium text-gray-600 hover:text-gray-900">Reviews</a>
          </div>

          <div className="hidden md:flex items-center gap-3">
            <a href="#pricing" className="btn-primary text-sm">
              Get Started Free
            </a>
          </div>

          <button className="md:hidden p-2" onClick={() => setMobileOpen(!mobileOpen)}>
            {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div className="md:hidden bg-white border-t border-gray-100 px-4 py-4 space-y-3">
          <a href="#features" className="block text-sm font-medium text-gray-600" onClick={() => setMobileOpen(false)}>Features</a>
          <a href="#how-it-works" className="block text-sm font-medium text-gray-600" onClick={() => setMobileOpen(false)}>How It Works</a>
          <a href="#pricing" className="block text-sm font-medium text-gray-600" onClick={() => setMobileOpen(false)}>Pricing</a>
          <a href="#pricing" className="btn-primary text-sm w-full text-center" onClick={() => setMobileOpen(false)}>Get Started Free</a>
        </div>
      )}
    </nav>
  );
}

// ─── Hero Section ───────────────────────────────────────────────────

function Hero() {
  return (
    <section className="pt-24 pb-16 md:pt-32 md:pb-24 bg-gradient-to-b from-green-50 to-white overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 bg-green-100 text-green-700 px-4 py-1.5 rounded-full text-sm font-medium mb-6">
            <Zap className="w-4 h-4" />
            Built for Indian Businesses
          </div>

          <h1 className="text-4xl md:text-6xl font-extrabold text-gray-900 leading-tight mb-6">
            Your 24/7 AI Receptionist,{' '}
            <span className="text-whatsapp">Right on WhatsApp</span>
          </h1>

          <p className="text-lg md:text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Let customers book appointments, ask questions, and get support — all through WhatsApp.
            No apps to download. No calls to miss. Just smart automation.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
            <a href="#pricing" className="btn-primary text-lg px-8 py-4">
              Start Free Trial
              <ArrowRight className="w-5 h-5 ml-2" />
            </a>
            <a href="#how-it-works" className="btn-secondary text-lg px-8 py-4">
              See How It Works
            </a>
          </div>

          <div className="flex items-center justify-center gap-6 text-sm text-gray-500">
            <div className="flex items-center gap-1">
              <CheckCircle2 className="w-4 h-4 text-whatsapp" />
              No credit card
            </div>
            <div className="flex items-center gap-1">
              <CheckCircle2 className="w-4 h-4 text-whatsapp" />
              50 free conversations
            </div>
            <div className="flex items-center gap-1">
              <CheckCircle2 className="w-4 h-4 text-whatsapp" />
              Setup in 5 minutes
            </div>
          </div>
        </div>

        {/* Hero visual — WhatsApp chat mockup */}
        <div className="mt-16 max-w-md mx-auto">
          <div className="bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden">
            <div className="bg-whatsapp px-4 py-3 flex items-center gap-3">
              <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                <Bot className="w-6 h-6 text-white" />
              </div>
              <div>
                <div className="text-white font-semibold text-sm">Lakshmi Salon</div>
                <div className="text-white/70 text-xs">AI Assistant • Online</div>
              </div>
            </div>
            <div className="p-4 space-y-3 bg-[#e5ddd5]">
              <div className="bg-white rounded-lg rounded-tl-none p-3 shadow-sm max-w-[80%]">
                <p className="text-sm text-gray-800">Hi! Welcome to Lakshmi Salon 💇‍♀️ How can I help you today?</p>
                <p className="text-[10px] text-gray-400 mt-1">10:30 AM</p>
              </div>
              <div className="bg-[#dcf8c6] rounded-lg rounded-tr-none p-3 shadow-sm max-w-[80%] ml-auto">
                <p className="text-sm text-gray-800">I want to book a haircut for tomorrow</p>
                <p className="text-[10px] text-gray-400 mt-1">10:31 AM ✓✓</p>
              </div>
              <div className="bg-white rounded-lg rounded-tl-none p-3 shadow-sm max-w-[80%]">
                <p className="text-sm text-gray-800">Great! Here are our services:</p>
                <p className="text-sm text-gray-800 mt-1">1. Haircut — ₹300 (30 min)<br/>2. Hair Color — ₹800 (60 min)<br/>3. Facial — ₹500 (45 min)</p>
                <p className="text-sm text-gray-800 mt-1">Which one?</p>
                <p className="text-[10px] text-gray-400 mt-1">10:31 AM</p>
              </div>
              <div className="bg-[#dcf8c6] rounded-lg rounded-tr-none p-3 shadow-sm max-w-[80%] ml-auto">
                <p className="text-sm text-gray-800">Haircut at 2 PM tomorrow</p>
                <p className="text-[10px] text-gray-400 mt-1">10:32 AM ✓✓</p>
              </div>
              <div className="bg-white rounded-lg rounded-tl-none p-3 shadow-sm max-w-[80%]">
                <p className="text-sm text-gray-800">✅ <strong>Booking Confirmed!</strong></p>
                <p className="text-sm text-gray-800 mt-1">📅 June 20, 2026<br/>⏰ 2:00 PM<br/>💇 Haircut</p>
                <p className="text-[10px] text-gray-400 mt-1">10:32 AM</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── Features Section ───────────────────────────────────────────────

const features = [
  {
    icon: Calendar,
    title: 'Smart Appointment Booking',
    description: 'Customers book, reschedule, and cancel appointments naturally through chat. No forms, no apps.',
    color: 'bg-blue-100 text-blue-600',
  },
  {
    icon: MessageCircle,
    title: 'Instant Customer Support',
    description: 'AI answers FAQs about services, pricing, hours, and location — 24/7 in Hindi, English, or any language.',
    color: 'bg-green-100 text-green-600',
  },
  {
    icon: IndianRupee,
    title: 'Pricing & Payments',
    description: 'Share service prices instantly. Integrate with UPI and payment links for seamless transactions.',
    color: 'bg-purple-100 text-purple-600',
  },
  {
    icon: Clock,
    title: 'Smart Reminders',
    description: 'Automatic booking reminders via WhatsApp. Reduce no-shows by up to 40%.',
    color: 'bg-orange-100 text-orange-600',
  },
  {
    icon: BarChart3,
    title: 'Business Insights',
    description: 'Daily reports on bookings, popular services, peak hours, and customer trends — delivered to your WhatsApp.',
    color: 'bg-pink-100 text-pink-600',
  },
  {
    icon: Shield,
    title: 'WhatsApp Native',
    description: 'Works entirely within WhatsApp. No new app for customers. No learning curve. Just chat.',
    color: 'bg-teal-100 text-teal-600',
  },
];

function Features() {
  return (
    <section id="features" className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="section-heading mb-4">Everything Your Business Needs</h2>
          <p className="section-subheading">
            From booking to business intelligence — all automated through WhatsApp.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="bg-white border border-gray-100 rounded-2xl p-6 hover:shadow-lg hover:border-brand-200 transition-all duration-300 group"
            >
              <div className={`w-12 h-12 rounded-xl ${feature.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                <feature.icon className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
              <p className="text-gray-600 text-sm leading-relaxed">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── How It Works ───────────────────────────────────────────────────

const steps = [
  {
    number: '01',
    title: 'Connect Your WhatsApp',
    description: 'Link your WhatsApp Business number in 2 minutes. No coding required.',
  },
  {
    number: '02',
    title: 'Set Up Your Services',
    description: 'Add your services, prices, and availability. Or let AI suggest them.',
  },
  {
    number: '03',
    title: 'Go Live',
    description: 'Customers start chatting. AI handles bookings, queries, and support 24/7.',
  },
  {
    number: '04',
    title: 'Grow Your Business',
    description: 'Get insights on bookings, trends, and customer preferences. Make smarter decisions.',
  },
];

function HowItWorks() {
  return (
    <section id="how-it-works" className="py-20 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="section-heading mb-4">Up & Running in 5 Minutes</h2>
          <p className="section-subheading">
            No developers. No complex setup. Just connect and go.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {steps.map((step) => (
            <div key={step.number} className="text-center">
              <div className="text-5xl font-extrabold text-brand-200 mb-4">{step.number}</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{step.title}</h3>
              <p className="text-gray-600 text-sm">{step.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── Pricing Section ────────────────────────────────────────────────

const plans = [
  {
    name: 'Free',
    price: '₹0',
    period: 'forever',
    description: 'Perfect for trying out',
    features: [
      '50 conversations/month',
      'Basic booking automation',
      '1 business',
      'WhatsApp support',
    ],
    cta: 'Start Free',
    highlighted: false,
  },
  {
    name: 'Pro',
    price: '₹999',
    period: '/month',
    description: 'For growing businesses',
    features: [
      'Unlimited conversations',
      'Smart booking + reminders',
      'Business analytics dashboard',
      'Multi-language support (Hindi, English)',
      'Custom branding',
      'Priority support',
    ],
    cta: 'Start Pro Trial',
    highlighted: true,
  },
  {
    name: 'Business',
    price: '₹2,499',
    period: '/month',
    description: 'For multi-location businesses',
    features: [
      'Everything in Pro',
      'Up to 5 business locations',
      'Team inbox',
      'API access',
      'Custom integrations',
      'Dedicated account manager',
    ],
    cta: 'Contact Sales',
    highlighted: false,
  },
];

function Pricing() {
  return (
    <section id="pricing" className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="section-heading mb-4">Simple, Transparent Pricing</h2>
          <p className="section-subheading">
            Start free. Scale when you're ready. No hidden fees.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`rounded-2xl p-8 ${
                plan.highlighted
                  ? 'bg-whatsapp text-white shadow-2xl scale-105 relative'
                  : 'bg-white border border-gray-200'
              }`}
            >
              {plan.highlighted && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-yellow-400 text-yellow-900 text-xs font-bold px-3 py-1 rounded-full">
                  MOST POPULAR
                </div>
              )}
              <div className={`text-sm font-semibold mb-1 ${plan.highlighted ? 'text-white/80' : 'text-gray-500'}`}>
                {plan.name}
              </div>
              <div className="flex items-baseline gap-1 mb-2">
                <span className={`text-4xl font-extrabold ${plan.highlighted ? 'text-white' : 'text-gray-900'}`}>
                  {plan.price}
                </span>
                <span className={`text-sm ${plan.highlighted ? 'text-white/70' : 'text-gray-500'}`}>
                  {plan.period}
                </span>
              </div>
              <p className={`text-sm mb-6 ${plan.highlighted ? 'text-white/80' : 'text-gray-500'}`}>
                {plan.description}
              </p>
              <ul className="space-y-3 mb-8">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2 text-sm">
                    <CheckCircle2 className={`w-5 h-5 flex-shrink-0 ${plan.highlighted ? 'text-white' : 'text-whatsapp'}`} />
                    <span className={plan.highlighted ? 'text-white' : 'text-gray-700'}>{feature}</span>
                  </li>
                ))}
              </ul>
              <button
                className={`w-full py-3 rounded-full font-semibold text-sm transition-colors ${
                  plan.highlighted
                    ? 'bg-white text-whatsapp hover:bg-gray-100'
                    : 'bg-gray-900 text-white hover:bg-gray-800'
                }`}
              >
                {plan.cta}
              </button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── Testimonials ───────────────────────────────────────────────────

const testimonials = [
  {
    name: 'Priya Sharma',
    business: 'Priya\'s Beauty Salon, Mumbai',
    text: 'My customers love booking on WhatsApp. I used to miss calls all the time. Now the AI handles everything and I focus on my work.',
    rating: 5,
  },
  {
    name: 'Rajesh Kumar',
    business: 'Kumar Dental Clinic, Bangalore',
    text: 'Setup took 10 minutes. Patients book appointments at midnight, early morning — anytime. My no-shows dropped by 35%.',
    rating: 5,
  },
  {
    name: 'Anita Desai',
    business: 'Anita\'s Tutorials, Pune',
    text: 'Parents ask about fees, timings, and availability. The bot answers instantly. I get fewer calls and more enrollments.',
    rating: 5,
  },
];

function Testimonials() {
  return (
    <section id="testimonials" className="py-20 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="section-heading mb-4">Loved by Indian Business Owners</h2>
          <p className="section-subheading">
            Join hundreds of businesses automating their WhatsApp.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {testimonials.map((t) => (
            <div key={t.name} className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
              <div className="flex gap-1 mb-4">
                {Array.from({ length: t.rating }).map((_, i) => (
                  <Star key={i} className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                ))}
              </div>
              <p className="text-gray-700 text-sm leading-relaxed mb-4">"{t.text}"</p>
              <div>
                <div className="font-semibold text-gray-900 text-sm">{t.name}</div>
                <div className="text-gray-500 text-xs">{t.business}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── CTA Section ────────────────────────────────────────────────────

function CTA() {
  return (
    <section className="py-20 bg-whatsapp">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
          Ready to Automate Your Business?
        </h2>
        <p className="text-lg text-white/80 mb-8 max-w-2xl mx-auto">
          Start with 50 free conversations. No credit card. No commitment.
          Set up in 5 minutes and let AI handle your WhatsApp.
        </p>
        <a
          href="#pricing"
          className="inline-flex items-center justify-center px-8 py-4 text-lg font-semibold text-whatsapp bg-white rounded-full hover:bg-gray-100 transition-colors shadow-lg"
        >
          Get Started Free
          <ArrowRight className="w-5 h-5 ml-2" />
        </a>
      </div>
    </section>
  );
}

// ─── Footer ─────────────────────────────────────────────────────────

function Footer() {
  return (
    <footer className="bg-gray-900 text-gray-400 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid md:grid-cols-4 gap-8 mb-8">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 bg-whatsapp rounded-lg flex items-center justify-center">
                <MessageCircle className="w-4 h-4 text-white" />
              </div>
              <span className="text-white font-bold">WhatsApp Agent</span>
            </div>
            <p className="text-sm">AI-powered WhatsApp automation for Indian businesses.</p>
          </div>
          <div>
            <h4 className="text-white font-semibold mb-3 text-sm">Product</h4>
            <ul className="space-y-2 text-sm">
              <li><a href="#features" className="hover:text-white">Features</a></li>
              <li><a href="#pricing" className="hover:text-white">Pricing</a></li>
              <li><a href="#" className="hover:text-white">Integrations</a></li>
            </ul>
          </div>
          <div>
            <h4 className="text-white font-semibold mb-3 text-sm">Company</h4>
            <ul className="space-y-2 text-sm">
              <li><a href="#" className="hover:text-white">About</a></li>
              <li><a href="#" className="hover:text-white">Blog</a></li>
              <li><a href="#" className="hover:text-white">Contact</a></li>
            </ul>
          </div>
          <div>
            <h4 className="text-white font-semibold mb-3 text-sm">Legal</h4>
            <ul className="space-y-2 text-sm">
              <li><a href="#" className="hover:text-white">Privacy Policy</a></li>
              <li><a href="#" className="hover:text-white">Terms of Service</a></li>
            </ul>
          </div>
        </div>
        <div className="border-t border-gray-800 pt-8 text-center text-sm">
          © 2026 WhatsApp Agent SaaS. All rights reserved. Made with ❤️ in India.
        </div>
      </div>
    </footer>
  );
}

// ─── Main Page ──────────────────────────────────────────────────────

export default function Home() {
  return (
    <>
      <Head>
        <title>WhatsApp Agent — AI Booking Assistant for Indian Businesses</title>
        <meta name="description" content="Turn WhatsApp into your 24/7 receptionist. AI-powered booking, customer support, and business insights for salons, clinics, tutors, and local businesses in India." />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <Navbar />
      <main>
        <Hero />
        <Features />
        <HowItWorks />
        <Pricing />
        <Testimonials />
        <CTA />
      </main>
      <Footer />
    </>
  );
}
