'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Briefcase, MapPin, Clock, Users, Heart, Zap, Globe, Award, Coffee, Laptop, Plane, GraduationCap } from 'lucide-react';

const Careers: React.FC = () => {
  const openPositions = [
    {
      title: "Senior AI Engineer",
      department: "Engineering",
      location: "San Francisco, CA / Remote",
      type: "Full-time",
      description: "Lead the development of our AI conversation engine and natural language processing systems.",
      requirements: ["5+ years in AI/ML", "Python, TensorFlow/PyTorch", "NLP experience", "PhD preferred"]
    },
    {
      title: "Product Manager",
      department: "Product",
      location: "San Francisco, CA",
      type: "Full-time", 
      description: "Drive product strategy and roadmap for our language learning platform.",
      requirements: ["3+ years product management", "EdTech experience", "Data-driven mindset", "User research skills"]
    },
    {
      title: "Frontend Developer",
      department: "Engineering",
      location: "Remote",
      type: "Full-time",
      description: "Build beautiful, responsive user interfaces using React and modern web technologies.",
      requirements: ["3+ years React/TypeScript", "UI/UX design sense", "Performance optimization", "Testing experience"]
    },
    {
      title: "Linguistics Researcher",
      department: "Research",
      location: "San Francisco, CA / Remote",
      type: "Full-time",
      description: "Research and develop language assessment methodologies and curriculum design.",
      requirements: ["PhD in Linguistics", "Second language acquisition", "Assessment design", "Research publications"]
    },
    {
      title: "DevOps Engineer",
      department: "Engineering",
      location: "Remote",
      type: "Full-time",
      description: "Scale our infrastructure to support millions of language learners worldwide.",
      requirements: ["AWS/GCP experience", "Kubernetes", "CI/CD pipelines", "Monitoring & observability"]
    },
    {
      title: "UX Designer",
      department: "Design",
      location: "San Francisco, CA / Remote",
      type: "Full-time",
      description: "Design intuitive and engaging user experiences for language learning.",
      requirements: ["3+ years UX design", "Figma/Sketch", "User research", "Mobile design experience"]
    }
  ];

  const benefits = [
    {
      icon: Heart,
      title: "Health & Wellness",
      description: "Comprehensive health, dental, and vision insurance plus wellness stipend."
    },
    {
      icon: Laptop,
      title: "Remote-First",
      description: "Work from anywhere with flexible hours and home office setup allowance."
    },
    {
      icon: GraduationCap,
      title: "Learning Budget",
      description: "$2,000 annual learning budget for courses, conferences, and books."
    },
    {
      icon: Plane,
      title: "Unlimited PTO",
      description: "Take the time you need to recharge with our unlimited vacation policy."
    },
    {
      icon: Coffee,
      title: "Team Retreats",
      description: "Quarterly team retreats and annual company-wide gatherings."
    },
    {
      icon: Award,
      title: "Equity Package",
      description: "Competitive equity package so you can share in our success."
    }
  ];

  const values = [
    {
      icon: Users,
      title: "Collaboration",
      description: "We believe the best ideas come from diverse teams working together."
    },
    {
      icon: Zap,
      title: "Innovation",
      description: "We're constantly pushing the boundaries of what's possible in language learning."
    },
    {
      icon: Globe,
      title: "Impact",
      description: "Our work helps millions of people connect across cultures and languages."
    },
    {
      icon: Heart,
      title: "Empathy",
      description: "We design with deep empathy for learners and their unique challenges."
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] text-white py-20">
        <div className="max-w-6xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center"
          >
            <div className="inline-flex items-center bg-white/20 rounded-full px-4 py-2 mb-6">
              <span className="text-sm font-medium">🚀 We're hiring!</span>
            </div>
            <h1 className="text-5xl font-bold mb-6">Join Our Mission</h1>
            <p className="text-xl text-white/90 max-w-3xl mx-auto leading-relaxed">
              Help us revolutionize language learning and connect people across cultures. 
              Build the future of AI-powered education with a passionate, global team.
            </p>
          </motion.div>
        </div>
      </div>

      {/* Why Join Us */}
      <div className="py-20">
        <div className="max-w-6xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-bold text-gray-800 mb-6">Why Language Tutor?</h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Join a team that's passionate about breaking down language barriers and making 
              quality education accessible to everyone.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {values.map((value, index) => (
              <motion.div
                key={value.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 * (index + 3) }}
                className="bg-white rounded-2xl p-8 shadow-lg border border-gray-200 text-center"
              >
                <div className="w-16 h-16 bg-[#4ECFBF]/10 rounded-xl flex items-center justify-center mx-auto mb-6">
                  <value.icon className="w-8 h-8 text-[#4ECFBF]" />
                </div>
                <h3 className="text-xl font-bold text-gray-800 mb-4">{value.title}</h3>
                <p className="text-gray-600 leading-relaxed">{value.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* Benefits */}
      <div className="py-20 bg-gray-50">
        <div className="max-w-6xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-bold text-gray-800 mb-6">Benefits & Perks</h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              We believe in taking care of our team so they can do their best work.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {benefits.map((benefit, index) => (
              <motion.div
                key={benefit.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 * (index + 3) }}
                className="bg-white rounded-2xl p-8 shadow-lg border border-gray-200"
              >
                <div className="w-12 h-12 bg-[#4ECFBF]/10 rounded-xl flex items-center justify-center mb-6">
                  <benefit.icon className="w-6 h-6 text-[#4ECFBF]" />
                </div>
                <h3 className="text-xl font-bold text-gray-800 mb-4">{benefit.title}</h3>
                <p className="text-gray-600 leading-relaxed">{benefit.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* Open Positions */}
      <div className="py-20">
        <div className="max-w-6xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-bold text-gray-800 mb-6">Open Positions</h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Find your next opportunity to make a meaningful impact in language education.
            </p>
          </motion.div>

          <div className="space-y-6">
            {openPositions.map((position, index) => (
              <motion.div
                key={position.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 * (index + 3) }}
                className="bg-white rounded-2xl p-8 shadow-lg border border-gray-200 hover:shadow-xl transition-shadow duration-300"
              >
                <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
                  <div className="flex-1">
                    <div className="flex flex-wrap items-center gap-4 mb-4">
                      <h3 className="text-2xl font-bold text-gray-800">{position.title}</h3>
                      <span className="px-3 py-1 bg-[#4ECFBF]/10 text-[#4ECFBF] rounded-full text-sm font-medium">
                        {position.department}
                      </span>
                    </div>
                    
                    <div className="flex flex-wrap items-center gap-6 mb-4 text-gray-600">
                      <div className="flex items-center">
                        <MapPin className="w-4 h-4 mr-2" />
                        <span className="text-sm">{position.location}</span>
                      </div>
                      <div className="flex items-center">
                        <Clock className="w-4 h-4 mr-2" />
                        <span className="text-sm">{position.type}</span>
                      </div>
                    </div>
                    
                    <p className="text-gray-600 mb-4 leading-relaxed">{position.description}</p>
                    
                    <div>
                      <h4 className="font-semibold text-gray-800 mb-2">Requirements:</h4>
                      <div className="flex flex-wrap gap-2">
                        {position.requirements.map((req, reqIndex) => (
                          <span
                            key={reqIndex}
                            className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
                          >
                            {req}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                  
                  <div className="mt-6 lg:mt-0 lg:ml-8">
                    <button className="w-full lg:w-auto px-8 py-3 bg-[#4ECFBF] hover:bg-[#3a9e92] text-white font-medium rounded-lg transition-colors duration-300 flex items-center justify-center">
                      <Briefcase className="w-4 h-4 mr-2" />
                      Apply Now
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* Application Process */}
      <div className="py-20 bg-gradient-to-r from-[#4ECFBF]/10 to-[#3a9e92]/10">
        <div className="max-w-6xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-bold text-gray-800 mb-6">Our Hiring Process</h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              We've designed our process to be transparent, efficient, and respectful of your time.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-4 gap-8">
            {[
              { step: "1", title: "Application", description: "Submit your resume and cover letter through our careers page." },
              { step: "2", title: "Phone Screen", description: "Brief conversation with our recruiting team about your background and interests." },
              { step: "3", title: "Technical Interview", description: "Role-specific technical assessment and problem-solving discussion." },
              { step: "4", title: "Team Interview", description: "Meet with team members and discuss culture fit and collaboration." }
            ].map((step, index) => (
              <motion.div
                key={step.step}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 * (index + 3) }}
                className="bg-white rounded-2xl p-6 shadow-lg border border-gray-200 text-center"
              >
                <div className="w-12 h-12 bg-[#4ECFBF] text-white rounded-full flex items-center justify-center mx-auto mb-4 font-bold text-lg">
                  {step.step}
                </div>
                <h3 className="text-xl font-bold text-gray-800 mb-3">{step.title}</h3>
                <p className="text-gray-600 leading-relaxed">{step.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* CTA */}
      <div className="py-20">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <h2 className="text-4xl font-bold text-gray-800 mb-6">Don't See Your Role?</h2>
            <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
              We're always looking for talented people who share our passion for language learning and education. 
              Send us your resume and let's talk!
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <a
                href="mailto:careers@languagetutor.ai"
                className="px-8 py-4 bg-[#4ECFBF] hover:bg-[#3a9e92] text-white font-medium rounded-lg transition-colors duration-300"
              >
                Send Resume
              </a>
              <a
                href="/about"
                className="px-8 py-4 border-2 border-[#4ECFBF] text-[#4ECFBF] hover:bg-[#4ECFBF] hover:text-white font-medium rounded-lg transition-all duration-300"
              >
                Learn More About Us
              </a>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default Careers;
