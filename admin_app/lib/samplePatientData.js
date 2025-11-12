// Sample patient appointments data structure
const samplePatientData = [
  {
    id: 17927,
    name: "Sonam Watts",
    age: 50,
    gender: "F",
    phone: "9501103553",
    email: "[email protected]",
    recentVisit: "Today",
    totalVisits: 1,
    time: "11:18 AM",
    wait: "3h 45m",
    status: "ON-GOING",
    purpose: "First Consultation",
    medicalHistory: {
      allergies: [],
      chronicConditions: [],
      currentMedications: []
    }
  },
  {
    id: 17931,
    name: "Krishna",
    age: 27,
    gender: "F",
    phone: "9501103554",
    email: "[email protected]",
    recentVisit: "Today",
    totalVisits: 1,
    time: "12:05 PM",
    wait: "2h 58m",
    status: "ON-GOING",
    purpose: "First Consultation",
    medicalHistory: {
      allergies: [],
      chronicConditions: [],
      currentMedications: []
    }
  },
  {
    id: 13801,
    name: "Manjeet Kaur",
    age: 35,
    gender: "F",
    phone: "9501103555",
    email: "[email protected]",
    recentVisit: "Today",
    totalVisits: 2,
    time: "1:51 PM",
    wait: "1h 12m",
    status: "ON-GOING",
    purpose: "Follow Up",
    medicalHistory: {
      allergies: ["Penicillin"],
      chronicConditions: ["Diabetes Type 2", "Hypothyroidism"],
      currentMedications: ["Metformin 500mg", "Levothyroxine 75mcg"]
    },
    previousVisits: [
      {
        date: "2025-10-15",
        complaints: ["Fatigue", "Weight gain"],
        diagnosis: ["E11.9 - Type 2 diabetes mellitus"],
        prescriptions: [
          {
            medicine: "Metformin",
            dosage: "500mg",
            frequency: "Twice Daily",
            duration: "30 days"
          }
        ]
      }
    ]
  },
  {
    id: 2233,
    name: "JASVEER KAUR",
    age: 62,
    gender: "F",
    phone: "9414298220",
    email: "[email protected]",
    recentVisit: "Today",
    totalVisits: 3,
    time: "1:58 PM",
    wait: "1h 5m",
    status: "ON-GOING",
    purpose: "Follow Up",
    medicalHistory: {
      allergies: [],
      chronicConditions: ["Hypertension"],
      currentMedications: ["Amlodipine 5mg"]
    }
  },
  {
    id: 17935,
    name: "Shakuntla",
    age: 65,
    gender: "F",
    phone: "9928922365",
    email: "[email protected]",
    recentVisit: "Today",
    totalVisits: 1,
    time: "2:03 PM",
    wait: "1h",
    status: "ON-GOING",
    purpose: "Follow Up",
    medicalHistory: {
      allergies: [],
      chronicConditions: [],
      currentMedications: []
    }
  },
  {
    id: 17934,
    name: "Om Prakash",
    age: 28,
    gender: "M",
    phone: "9799622217",
    email: "[email protected]",
    recentVisit: "--",
    totalVisits: 0,
    time: "1:54 PM",
    wait: "1h 9m",
    status: "BOOKED",
    purpose: "Follow Up",
    medicalHistory: {
      allergies: [],
      chronicConditions: [],
      currentMedications: []
    }
  }
];

window.samplePatientData = samplePatientData;

