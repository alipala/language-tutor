'use client';

import Image from "next/image";
import { Users, Target, Shield, Lightbulb, Heart, Globe, Mail, Phone, MapPin } from "lucide-react";

export default function AboutPage() {
  return (
    <div className="min-h-screen" style={{ backgroundColor: '#0A0A0F' }}>
      {/* Hero Section */}
      <section className="pt-28 sm:pt-32 pb-16 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-brand via-[#FFD63A] to-[#F75A5A] bg-clip-text text-transparent mb-6">
            About MyTaco AI
          </h1>
          <p className="text-xl text-white/60 leading-relaxed max-w-3xl mx-auto mb-8">
            My Taco - AI Language Coach revolutionises language learning by offering AI-powered conversations,
            personalised feedback, and adaptive learning experiences. It enables users to master any language
            confidently through tailored practice and skill development.
          </p>
          <div className="rounded-2xl p-8 border border-white/[0.10]" style={{ backgroundColor: '#13131F' }}>
            <h2 className="text-2xl font-bold text-white mb-4">Our Mission</h2>
            <p className="text-white/60 leading-relaxed">
              Imagine mastering a new language just by having real conversations, right from home. My Taco AI
              combines advanced AI with live, voice-based tutors, providing instant feedback and tailored learning
              plans based on your speaking skills. Experience authentic practice with diverse voices and truly
              accelerate your fluency—not by memorizing, but by speaking. Start now and see for yourself how
              interactive AI can help you speak with confidence every single day.
            </p>
          </div>
        </div>
      </section>

      {/* Our Values Section */}
      <section className="py-16 px-4" style={{ backgroundColor: '#0E0E1A' }}>
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-white mb-12">Our Values</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Accessibility Value */}
            <div className="bg-gradient-to-br from-brand/10 to-brand/5 rounded-2xl p-8 border border-brand/20 hover:border-brand/40 transition-all duration-300 hover:shadow-lg hover:shadow-brand/5">
              <div className="w-12 h-12 bg-brand rounded-full flex items-center justify-center mb-6">
                <Globe className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-white mb-4">Accessibility for All</h3>
              <p className="text-white/60 leading-relaxed">
                We believe language learning should be accessible to everyone, regardless of their schedule,
                budget, or location. Our AI-powered platform breaks down traditional barriers to language
                education, making quality learning available 24/7 at an affordable price.
              </p>
            </div>

            {/* Innovation Value */}
            <div className="bg-gradient-to-br from-[#FFD63A]/10 to-[#FFD63A]/5 rounded-2xl p-8 border border-[#FFD63A]/20 hover:border-[#FFD63A]/40 transition-all duration-300 hover:shadow-lg hover:shadow-[#FFD63A]/5">
              <div className="w-12 h-12 bg-[#FFD63A] rounded-full flex items-center justify-center mb-6">
                <Lightbulb className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-white mb-4">AI-Powered Innovation</h3>
              <p className="text-white/60 leading-relaxed">
                We harness cutting-edge AI technology to create personalized learning experiences that adapt
                to your unique learning style, pace, and goals. Our real-time voice interaction and intelligent
                feedback systems revolutionize how languages are learned.
              </p>
            </div>

            {/* Empathy Value */}
            <div className="bg-gradient-to-br from-[#F75A5A]/10 to-[#F75A5A]/5 rounded-2xl p-8 border border-[#F75A5A]/20 hover:border-[#F75A5A]/40 transition-all duration-300 hover:shadow-lg hover:shadow-[#F75A5A]/5">
              <div className="w-12 h-12 bg-[#F75A5A] rounded-full flex items-center justify-center mb-6">
                <Heart className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-white mb-4">Empathy & Understanding</h3>
              <p className="text-white/60 leading-relaxed">
                As parents and immigrants ourselves, we understand the challenges of learning a new language
                while juggling work, family, and community responsibilities. We build with empathy, creating
                solutions that fit into real life.
              </p>
            </div>

            {/* Quality Value */}
            <div className="bg-gradient-to-br from-[#FFA955]/10 to-[#FFA955]/5 rounded-2xl p-8 border border-[#FFA955]/20 hover:border-[#FFA955]/40 transition-all duration-300 hover:shadow-lg hover:shadow-[#FFA955]/5">
              <div className="w-12 h-12 bg-[#FFA955] rounded-full flex items-center justify-center mb-6">
                <Target className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-white mb-4">Quality & Excellence</h3>
              <p className="text-white/60 leading-relaxed">
                With over 15 years of enterprise software development experience, we bring professional-grade
                quality to language learning. Every feature is meticulously crafted to deliver exceptional
                user experiences and measurable learning outcomes.
              </p>
            </div>

            {/* Responsible AI Value */}
            <div className="bg-gradient-to-br from-brand/10 to-[#F75A5A]/5 rounded-2xl p-8 border border-brand/20 hover:border-[#F75A5A]/20 transition-all duration-300 hover:shadow-lg">
              <div className="w-12 h-12 bg-gradient-to-r from-brand to-[#F75A5A] rounded-full flex items-center justify-center mb-6">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-white mb-4">Responsible AI</h3>
              <p className="text-white/60 leading-relaxed">
                We are committed to ethical AI development and responsible data usage. Our AI systems are
                designed with privacy-first principles, transparent algorithms, and bias mitigation. We ensure
                our technology enhances human learning without replacing human connection.
              </p>
            </div>

            {/* Data Privacy Value */}
            <div className="bg-gradient-to-br from-[#FFD63A]/10 to-[#FFA955]/5 rounded-2xl p-8 border border-[#FFD63A]/20 hover:border-[#FFA955]/20 transition-all duration-300 hover:shadow-lg">
              <div className="w-12 h-12 bg-gradient-to-r from-[#FFD63A] to-[#FFA955] rounded-full flex items-center justify-center mb-6">
                <Users className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-white mb-4">Data Privacy & Trust</h3>
              <p className="text-white/60 leading-relaxed">
                Your learning data and personal information are sacred to us. We implement enterprise-grade
                security measures, transparent data practices, and give you full control over your information.
                Your trust is the foundation of our relationship.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Our Story Section */}
      <section className="py-16 px-4" style={{ backgroundColor: '#0A0A0F' }}>
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-white mb-12">Our Story</h2>
          <div className="rounded-2xl p-8 border border-white/[0.10]" style={{ backgroundColor: '#13131F' }}>
            <p className="text-white/60 leading-relaxed mb-6">
              The idea for MyTaco AI was born from our personal struggles as immigrant parents in the Netherlands.
              We officially started building this application in 2025, but the concept had been brewing in our minds
              for years.
            </p>
            <p className="text-white/60 leading-relaxed mb-6">
              As two busy parents juggling demanding careers, raising children, and integrating into Dutch society,
              we experienced firsthand the challenges of finding time to learn a new language. Between work commitments,
              caring for our kids, understanding the Dutch system, and actively participating in our local community,
              traditional language learning methods simply didn't fit our reality.
            </p>
            <p className="text-white/60 leading-relaxed mb-6">
              The turning point came during our kids' hockey club activities. As active parents engaging with other
              families, we often found ourselves in social situations where English was sufficient, but we felt
              something was missing. We experienced that subtle sense of being on the outside—not because we weren't
              welcome, but because language barriers prevented us from fully connecting and contributing to our community.
            </p>
            <p className="text-white/60 leading-relaxed mb-6">
              This personal frustration, combined with our extensive experience in enterprise software development
              and business solutions, sparked the vision for MyTaco AI (Language Coach - "Taal Coach" in Dutch).
              Having worked for major enterprise companies throughout our careers, we possessed the technical expertise
              and business acumen to transform our personal challenge into a solution that could help millions of others.
            </p>
            <p className="text-white/60 leading-relaxed">
              We're passionate about helping people who face the same struggles we did—parents, professionals, and
              immigrants who want to learn but can't find the time or afford expensive traditional methods. MyTaco AI
              represents our commitment to making language learning accessible, affordable, and effective for everyone,
              regardless of their circumstances. Because we believe that language should connect us, not divide us.
            </p>
          </div>
        </div>
      </section>

      {/* Meet Our Team Section */}
      <section className="py-16 px-4" style={{ backgroundColor: '#0E0E1A' }}>
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-white mb-12">Meet Our Team</h2>

          {/* Founders */}
          <div className="grid md:grid-cols-2 gap-8 mb-12">
            {/* Maikel */}
            <div className="bg-gradient-to-br from-brand/5 to-[#FFD63A]/5 rounded-2xl p-8 border border-white/[0.10] hover:shadow-lg hover:shadow-black/20 transition-all duration-300">
              <div className="text-center mb-6">
                <a
                  href="https://www.linkedin.com/in/maikel-kuppens-32129420/"
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label="Maikel Kuppens on LinkedIn"
                  className="group block w-24 h-24 rounded-full mx-auto mb-4 overflow-hidden bg-gradient-to-r from-brand to-[#FFD63A] ring-2 ring-white/10 hover:ring-brand/60 transition-all duration-300"
                >
                  <Image
                    src="/images/team/maikel-kuppens.jpg"
                    alt="Maikel Kuppens"
                    width={96}
                    height={96}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                </a>
                <h3 className="text-xl font-bold text-white">Maikel Kuppens</h3>
                <p className="text-brand font-semibold">Co-Founder &amp; Growth</p>
                <p className="text-white/40 text-xs mt-0.5">AI Consulting &amp; Business Development</p>
              </div>
              <p className="text-white/60 leading-relaxed">
                Based in Amsterdam, Maikel is an AI consultant and growth strategist who helps businesses tap into the
                world of AI—turning emerging technology into real, practical solutions. Through his work with TAP Agency,
                he supports companies in automating and elevating their operations with AI. With a strong background in
                sales, business development, and high-ticket partnerships, Maikel drives MyTaco AI's growth and brings a
                relentless commercial focus on getting our speaking coach into the hands of learners everywhere.
              </p>
            </div>

            {/* Ali */}
            <div className="bg-gradient-to-br from-[#F75A5A]/5 to-[#FFA955]/5 rounded-2xl p-8 border border-white/[0.10] hover:shadow-lg hover:shadow-black/20 transition-all duration-300">
              <div className="text-center mb-6">
                <a
                  href="https://www.linkedin.com/in/alipala/"
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label="Ali Pala on LinkedIn"
                  className="group block w-24 h-24 rounded-full mx-auto mb-4 overflow-hidden bg-gradient-to-r from-[#F75A5A] to-[#FFA955] ring-2 ring-white/10 hover:ring-[#F75A5A]/60 transition-all duration-300"
                >
                  <Image
                    src="/images/team/ali-pala.jpg"
                    alt="Ali Pala"
                    width={96}
                    height={96}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                </a>
                <h3 className="text-xl font-bold text-white">Ali Pala</h3>
                <p className="text-[#F75A5A] font-semibold">Co-Founder &amp; CTO</p>
                <p className="text-white/40 text-xs mt-0.5">Voice AI &amp; Backend Engineering</p>
              </div>
              <p className="text-white/60 leading-relaxed">
                Ali is the technical co-founder behind MyTaco AI, with 15+ years building backend and AI systems.
                He architects the real-time voice stack — OpenAI&apos;s Realtime API, Azure Speech Services, and the
                speech-to-text / text-to-speech pipelines that let learners hold a natural conversation with sub-second
                latency. His focus is on making agentic, voice-first AI genuinely reliable in production: orchestrating
                LLM agents and tool use, hardening them with guardrails, and designing self-healing, observable services
                that stay fast and dependable at scale. An active GenAI contributor who cares less about demos and more
                about how these systems actually behave under real load, Ali sets the engineering bar for the platform.
              </p>
            </div>
          </div>

          {/* AI Agents */}
          <div className="grid md:grid-cols-2 gap-8">
            {/* Educational Psychologist AI */}
            <div className="bg-gradient-to-br from-brand/10 to-brand/5 rounded-2xl p-8 border border-brand/20">
              <div className="text-center mb-6">
                <div className="w-20 h-20 rounded-full mx-auto mb-4 overflow-hidden bg-brand/20 ring-2 ring-brand/40">
                  <Image
                    src="/images/team/dr-elena.png"
                    alt="Dr. Elena Psyche"
                    width={80}
                    height={80}
                    className="w-full h-full object-cover"
                  />
                </div>
                <h3 className="text-lg font-bold text-white">Dr. Elena Psyche</h3>
                <p className="text-brand font-semibold">Educational Psychologist AI Agent</p>
              </div>
              <p className="text-white/60 leading-relaxed text-sm">
                Our specialized AI agent focused on understanding learning psychology and emotional barriers to
                language acquisition. Dr. Elena analyzes user behavior patterns, identifies learning obstacles,
                and provides personalized motivational support. She ensures that our platform addresses not just
                the cognitive aspects of learning, but also the emotional and psychological factors that influence
                language learning success.
              </p>
            </div>

            {/* Adaptive Learning Expert AI */}
            <div className="bg-gradient-to-br from-[#FFD63A]/10 to-[#FFD63A]/5 rounded-2xl p-8 border border-[#FFD63A]/20">
              <div className="text-center mb-6">
                <div className="w-20 h-20 rounded-full mx-auto mb-4 overflow-hidden bg-[#FFD63A]/20 ring-2 ring-[#FFD63A]/40">
                  <Image
                    src="/images/team/prof-adam.png"
                    alt="Prof. Adam Learning"
                    width={80}
                    height={80}
                    className="w-full h-full object-cover"
                  />
                </div>
                <h3 className="text-lg font-bold text-white">Prof. Adam Learning</h3>
                <p className="text-[#FFD63A] font-semibold">Adaptive Learning Expert AI Agent</p>
              </div>
              <p className="text-white/60 leading-relaxed text-sm">
                Our advanced AI agent specializing in adaptive learning algorithms and personalized curriculum
                design. Prof. Adam continuously analyzes user performance data, learning patterns, and progress
                rates to dynamically adjust difficulty levels, content selection, and learning paths. He ensures
                that every user receives a truly personalized learning experience that evolves with their progress.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Journey Highlights Section */}
      <section className="py-16 px-4" style={{ backgroundColor: '#0A0A0F' }}>
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-white mb-12">Our Journey So Far</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center rounded-2xl p-6 border border-white/[0.10]" style={{ backgroundColor: '#13131F' }}>
              <div className="w-16 h-16 bg-gradient-to-r from-brand to-[#FFD63A] rounded-full mx-auto mb-4 flex items-center justify-center">
                <Lightbulb className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Innovation Launch</h3>
              <p className="text-white/60">
                Successfully launched with cutting-edge AI voice technology and real-time conversation capabilities.
              </p>
            </div>

            <div className="text-center rounded-2xl p-6 border border-white/[0.10]" style={{ backgroundColor: '#13131F' }}>
              <div className="w-16 h-16 bg-gradient-to-r from-[#F75A5A] to-[#FFA955] rounded-full mx-auto mb-4 flex items-center justify-center">
                <Users className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Growing Community</h3>
              <p className="text-white/60">
                Building a passionate community of learners from diverse backgrounds, all sharing the goal of language mastery.
              </p>
            </div>

            <div className="text-center rounded-2xl p-6 border border-white/[0.10]" style={{ backgroundColor: '#13131F' }}>
              <div className="w-16 h-16 bg-gradient-to-r from-[#FFD63A] to-brand rounded-full mx-auto mb-4 flex items-center justify-center">
                <Target className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Continuous Evolution</h3>
              <p className="text-white/60">
                Constantly improving our AI models and learning algorithms based on user feedback and latest research.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Get in Touch Section */}
      <section className="py-16 px-4" style={{ backgroundColor: '#0E0E1A' }}>
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-8">Get in Touch</h2>
          <p className="text-xl text-white/60 mb-12">
            Have questions about MyTaco AI? We'd love to hear from you!
          </p>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 bg-brand rounded-full flex items-center justify-center mb-4">
                <Mail className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Email</h3>
              <p className="text-white/60">hello@mytacoai.com</p>
            </div>

            <div className="flex flex-col items-center">
              <div className="w-16 h-16 bg-[#FFD63A] rounded-full flex items-center justify-center mb-4">
                <Phone className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Phone</h3>
              <p className="text-white/60">+31 6 21 18 55 93</p>
            </div>

            <div className="flex flex-col items-center">
              <div className="w-16 h-16 bg-[#F75A5A] rounded-full flex items-center justify-center mb-4">
                <MapPin className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Location</h3>
              <p className="text-white/60">Amsterdam, Netherlands</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
