'use client';

import { Shield, Eye, Users, Lock, CheckCircle, Brain, Heart, Globe, Award, BookOpen, Target, Scale, UserCheck, Lightbulb, Compass } from "lucide-react";

export default function ResponsibleAIPage() {
  return (
    <div className="min-h-screen" style={{ backgroundColor: '#0A0A0F' }}>
      {/* Hero Section */}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-brand via-[#FFD63A] to-[#F75A5A] bg-clip-text text-transparent mb-6">
            Responsible AI
          </h1>
          <p className="text-xl text-white/60 leading-relaxed max-w-3xl mx-auto mb-8">
            Our commitment to developing ethical, transparent, and accountable AI systems that enhance
            human learning while respecting privacy, fairness, and individual dignity. We believe AI
            should serve humanity, not the other way around.
          </p>
          <div className="rounded-2xl p-8 border border-white/[0.10]" style={{ backgroundColor: '#13131F' }}>
            <h2 className="text-2xl font-bold text-white mb-4">What We Think</h2>
            <p className="text-white/60 leading-relaxed">
              AI has the power to revolutionize education and break down barriers to learning. However,
              with this power comes great responsibility. We are committed to building AI systems that
              are fair, transparent, secure, and beneficial to all learners, regardless of their background,
              abilities, or circumstances. Our approach to responsible AI isn't just about compliance—it's
              about creating technology that truly serves human flourishing.
            </p>
          </div>
        </div>
      </section>

      {/* Our AI Principles Section */}
      <section className="py-16 px-4" style={{ backgroundColor: '#0E0E1A' }}>
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-white mb-12">Our AI Principles</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Fairness & Bias Mitigation */}
            <div className="bg-gradient-to-br from-brand/10 to-brand/5 rounded-2xl p-8 border border-brand/20 hover:border-brand/40 transition-all duration-300 hover:shadow-lg hover:shadow-brand/5">
              <div className="w-12 h-12 bg-brand rounded-full flex items-center justify-center mb-6">
                <Scale className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-white mb-4">Fairness & Bias Mitigation</h3>
              <p className="text-white/60 leading-relaxed">
                We ensure our AI treats all learners fairly, regardless of their background, gender, age,
                or native language. Our systems undergo regular bias audits and we use diverse training
                data to prevent discrimination and promote equitable learning experiences.
              </p>
            </div>

            {/* Transparency & Explainability */}
            <div className="bg-gradient-to-br from-[#FFD63A]/10 to-[#FFD63A]/5 rounded-2xl p-8 border border-[#FFD63A]/20 hover:border-[#FFD63A]/40 transition-all duration-300 hover:shadow-lg hover:shadow-[#FFD63A]/5">
              <div className="w-12 h-12 bg-[#FFD63A] rounded-full flex items-center justify-center mb-6">
                <Eye className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-white mb-4">Transparency & Explainability</h3>
              <p className="text-white/60 leading-relaxed">
                Our AI provides clear explanations for its recommendations and feedback. Learners understand
                how their progress is measured and why specific suggestions are made. We believe in making
                AI decisions understandable and accessible to everyone.
              </p>
            </div>

            {/* Privacy & Security */}
            <div className="bg-gradient-to-br from-[#F75A5A]/10 to-[#F75A5A]/5 rounded-2xl p-8 border border-[#F75A5A]/20 hover:border-[#F75A5A]/40 transition-all duration-300 hover:shadow-lg hover:shadow-[#F75A5A]/5">
              <div className="w-12 h-12 bg-[#F75A5A] rounded-full flex items-center justify-center mb-6">
                <Lock className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-white mb-4">Privacy & Security</h3>
              <p className="text-white/60 leading-relaxed">
                Your learning data is sacred to us. We implement end-to-end encryption, follow data
                minimization principles, and give you complete control over your personal information.
                We collect only what's necessary and protect it with enterprise-grade security.
              </p>
            </div>

            {/* Accountability & Governance */}
            <div className="bg-gradient-to-br from-[#FFA955]/10 to-[#FFA955]/5 rounded-2xl p-8 border border-[#FFA955]/20 hover:border-[#FFA955]/40 transition-all duration-300 hover:shadow-lg hover:shadow-[#FFA955]/5">
              <div className="w-12 h-12 bg-[#FFA955] rounded-full flex items-center justify-center mb-6">
                <UserCheck className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-white mb-4">Accountability & Governance</h3>
              <p className="text-white/60 leading-relaxed">
                We maintain clear ownership of our AI systems and provide channels for feedback and
                concerns. Our team is accountable for AI decisions, and we have established processes
                for addressing issues and continuously improving our systems.
              </p>
            </div>

            {/* Reliability & Safety */}
            <div className="bg-gradient-to-br from-brand/10 to-[#F75A5A]/5 rounded-2xl p-8 border border-brand/20 hover:border-[#F75A5A]/20 transition-all duration-300 hover:shadow-lg">
              <div className="w-12 h-12 bg-gradient-to-r from-brand to-[#F75A5A] rounded-full flex items-center justify-center mb-6">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-white mb-4">Reliability & Safety</h3>
              <p className="text-white/60 leading-relaxed">
                Our AI undergoes extensive testing across diverse scenarios and user groups. We include
                safety mechanisms for unexpected situations and continuously monitor performance to ensure
                reliable, consistent experiences for all learners.
              </p>
            </div>

            {/* Inclusiveness & Accessibility */}
            <div className="bg-gradient-to-br from-[#FFD63A]/10 to-[#FFA955]/5 rounded-2xl p-8 border border-[#FFD63A]/20 hover:border-[#FFA955]/20 transition-all duration-300 hover:shadow-lg">
              <div className="w-12 h-12 bg-gradient-to-r from-[#FFD63A] to-[#FFA955] rounded-full flex items-center justify-center mb-6">
                <Users className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-bold text-white mb-4">Inclusiveness & Accessibility</h3>
              <p className="text-white/60 leading-relaxed">
                We design our AI to be accessible to learners with diverse abilities and support multiple
                learning styles. Our technology empowers everyone to learn effectively, ensuring that
                language learning is truly accessible to all.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Our Approach Section */}
      <section className="py-16 px-4" style={{ backgroundColor: '#0A0A0F' }}>
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-white mb-12">Our Approach to Responsible AI</h2>
          <div className="rounded-2xl p-8 border border-white/[0.10]" style={{ backgroundColor: '#13131F' }}>
            <div className="grid md:grid-cols-2 gap-8">
              <div>
                <h3 className="text-xl font-bold text-white mb-4">Ethics by Design</h3>
                <p className="text-white/60 leading-relaxed mb-6">
                  We integrate ethical considerations from the earliest stages of AI development. Every
                  feature, algorithm, and decision is evaluated through the lens of our responsible AI
                  principles before implementation.
                </p>

                <h3 className="text-xl font-bold text-white mb-4">Continuous Monitoring</h3>
                <p className="text-white/60 leading-relaxed">
                  Our AI systems are continuously monitored for bias, fairness, and performance. We
                  conduct regular audits and assessments to ensure our technology remains aligned with
                  our ethical standards and user needs.
                </p>
              </div>

              <div>
                <h3 className="text-xl font-bold text-white mb-4">Human-Centered AI</h3>
                <p className="text-white/60 leading-relaxed mb-6">
                  Our AI is designed to enhance human learning, not replace human judgment or connection.
                  We believe in augmenting human capabilities while preserving the essential human elements
                  of education and personal growth.
                </p>

                <h3 className="text-xl font-bold text-white mb-4">Community Engagement</h3>
                <p className="text-white/60 leading-relaxed">
                  We actively engage with our community, researchers, and ethicists to continuously
                  improve our responsible AI practices. Your feedback and concerns help shape the
                  future of our technology.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Implementation in Practice Section */}
      <section className="py-16 px-4" style={{ backgroundColor: '#0E0E1A' }}>
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-white mb-12">Implementation in Practice</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* Personalized Learning */}
            <div className="text-center bg-gradient-to-br from-brand/5 to-brand/10 rounded-2xl p-6 border border-brand/20">
              <div className="w-16 h-16 bg-brand rounded-full mx-auto mb-4 flex items-center justify-center">
                <Brain className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Personalized Learning</h3>
              <p className="text-white/60 text-sm">
                Our AI adapts to individual learning styles while ensuring fair treatment across all
                demographic groups and learning preferences.
              </p>
            </div>

            {/* Bias-Free Assessment */}
            <div className="text-center bg-gradient-to-br from-[#FFD63A]/5 to-[#FFD63A]/10 rounded-2xl p-6 border border-[#FFD63A]/20">
              <div className="w-16 h-16 bg-[#FFD63A] rounded-full mx-auto mb-4 flex items-center justify-center">
                <Target className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Bias-Free Assessment</h3>
              <p className="text-white/60 text-sm">
                Regular audits ensure our AI assessments are fair and unbiased across different
                languages, cultures, and learning backgrounds.
              </p>
            </div>

            {/* Transparent Feedback */}
            <div className="text-center bg-gradient-to-br from-[#F75A5A]/5 to-[#F75A5A]/10 rounded-2xl p-6 border border-[#F75A5A]/20">
              <div className="w-16 h-16 bg-[#F75A5A] rounded-full mx-auto mb-4 flex items-center justify-center">
                <Lightbulb className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Transparent Feedback</h3>
              <p className="text-white/60 text-sm">
                Learners receive clear explanations for AI recommendations and can understand
                how their progress is measured and evaluated.
              </p>
            </div>

            {/* Privacy-First Design */}
            <div className="text-center bg-gradient-to-br from-[#FFA955]/5 to-[#FFA955]/10 rounded-2xl p-6 border border-[#FFA955]/20">
              <div className="w-16 h-16 bg-[#FFA955] rounded-full mx-auto mb-4 flex items-center justify-center">
                <Lock className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Privacy-First Design</h3>
              <p className="text-white/60 text-sm">
                All learning data is encrypted and processed with strict privacy controls,
                giving users full control over their information.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Our Commitments Section */}
      <section className="py-16 px-4" style={{ backgroundColor: '#0A0A0F' }}>
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-white mb-12">Our Ongoing Commitments</h2>
          <div className="grid md:grid-cols-2 gap-8">
            <div className="rounded-2xl p-8 border border-white/[0.10]" style={{ backgroundColor: '#13131F' }}>
              <div className="flex items-center mb-4">
                <div className="w-12 h-12 bg-brand rounded-full flex items-center justify-center mr-4">
                  <Heart className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-bold text-white">Learner-Centric AI</h3>
              </div>
              <p className="text-white/60 leading-relaxed">
                Our AI is designed to enhance human learning, not replace human judgment. We prioritize
                learner well-being and educational outcomes above all else.
              </p>
            </div>

            <div className="rounded-2xl p-8 border border-white/[0.10]" style={{ backgroundColor: '#13131F' }}>
              <div className="flex items-center mb-4">
                <div className="w-12 h-12 bg-[#FFD63A] rounded-full flex items-center justify-center mr-4">
                  <BookOpen className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-bold text-white">Continuous Improvement</h3>
              </div>
              <p className="text-white/60 leading-relaxed">
                We continuously evolve our responsible AI practices based on the latest research,
                user feedback, and emerging best practices in the field.
              </p>
            </div>

            <div className="rounded-2xl p-8 border border-white/[0.10]" style={{ backgroundColor: '#13131F' }}>
              <div className="flex items-center mb-4">
                <div className="w-12 h-12 bg-[#F75A5A] rounded-full flex items-center justify-center mr-4">
                  <Globe className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-bold text-white">Open Dialogue</h3>
              </div>
              <p className="text-white/60 leading-relaxed">
                We engage with the community, researchers, and policymakers on AI ethics, contributing
                to the broader conversation about responsible AI development.
              </p>
            </div>

            <div className="rounded-2xl p-8 border border-white/[0.10]" style={{ backgroundColor: '#13131F' }}>
              <div className="flex items-center mb-4">
                <div className="w-12 h-12 bg-[#FFA955] rounded-full flex items-center justify-center mr-4">
                  <Award className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-bold text-white">Regulatory Compliance</h3>
              </div>
              <p className="text-white/60 leading-relaxed">
                We comply with emerging AI regulations and industry best practices, staying ahead
                of regulatory requirements to ensure responsible deployment.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Call to Action Section */}
      <section className="py-16 px-4" style={{ backgroundColor: '#0E0E1A' }}>
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-8">Join the Conversation</h2>
          <p className="text-xl text-white/60 mb-12">
            Responsible AI requires collaboration across the entire community. We welcome your thoughts,
            concerns, and suggestions as we continue to build AI that serves humanity.
          </p>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 bg-brand rounded-full flex items-center justify-center mb-4">
                <Users className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Community Feedback</h3>
              <p className="text-white/60 text-center">
                Share your experiences and suggestions to help us improve our responsible AI practices.
              </p>
            </div>

            <div className="flex flex-col items-center">
              <div className="w-16 h-16 bg-[#FFD63A] rounded-full flex items-center justify-center mb-4">
                <BookOpen className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Research Collaboration</h3>
              <p className="text-white/60 text-center">
                Partner with us on research initiatives to advance responsible AI in education.
              </p>
            </div>

            <div className="flex flex-col items-center">
              <div className="w-16 h-16 bg-[#F75A5A] rounded-full flex items-center justify-center mb-4">
                <Shield className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Ethics Consultation</h3>
              <p className="text-white/60 text-center">
                Consult with our ethics team about AI concerns or responsible development practices.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
