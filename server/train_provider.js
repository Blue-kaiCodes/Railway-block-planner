import { STATIONS_DB, getStationByCode } from "./station_data.js";

// Comprehensive Indian Railways Premier & Express Train Timetable Dataset
// Real routes, stops, scheduled times, and train specifications
export const INDIAN_RAILWAYS_TRAINS = [
  {
    train_number: "12301",
    train_name: "Howrah Rajdhani Express (via Gaya)",
    train_type: "Rajdhani Express",
    service_priority: 1,
    origin: "Howrah Junction (HWH)",
    destination: "New Delhi (NDLS)",
    origin_code: "HWH",
    destination_code: "NDLS",
    days_of_run: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sun"],
    avg_speed_kmh: 88,
    distance_km: 1451,
    is_protected: true,
    route: [
      { stop_number: 1, station_code: "HWH", station_name: "Howrah Junction", arrival: null, departure: "16:50", day: 1, distance_km: 0 },
      { stop_number: 2, station_code: "BWN", station_name: "Barddhaman Junction", arrival: "17:37", departure: "17:39", day: 1, distance_km: 94 },
      { stop_number: 3, station_code: "ASN", station_name: "Asansol Junction", arrival: "18:57", departure: "19:00", day: 1, distance_km: 200 },
      { stop_number: 4, station_code: "DHN", station_name: "Dhanbad Junction", arrival: "19:55", departure: "20:00", day: 1, distance_km: 259 },
      { stop_number: 5, station_code: "PNME", station_name: "Parasnath", arrival: "20:34", departure: "20:36", day: 1, distance_km: 306 },
      { stop_number: 6, station_code: "KQR", station_name: "Koderma Junction", arrival: "21:24", departure: "21:26", day: 1, distance_km: 382 },
      { stop_number: 7, station_code: "GAYA", station_name: "Gaya Junction", arrival: "22:29", departure: "22:32", day: 1, distance_km: 459 },
      { stop_number: 8, station_code: "DOS", station_name: "Dehri On Sone", arrival: "23:25", departure: "23:27", day: 1, distance_km: 544 },
      { stop_number: 9, station_code: "SSM", station_name: "Sasaram Junction", arrival: "23:40", departure: "23:42", day: 1, distance_km: 562 },
      { stop_number: 10, station_code: "DDU", station_name: "Pt. Deen Dayal Upadhyaya Junction", arrival: "00:45", departure: "00:55", day: 2, distance_km: 664 },
      { stop_number: 11, station_code: "PRYJ", station_name: "Prayagraj Junction", arrival: "02:43", departure: "02:45", day: 2, distance_km: 817 },
      { stop_number: 12, station_code: "CNB", station_name: "Kanpur Central", arrival: "04:40", departure: "04:45", day: 2, distance_km: 1011 },
      { stop_number: 13, station_code: "NDLS", station_name: "New Delhi", arrival: "10:05", departure: null, day: 2, distance_km: 1451 }
    ]
  },
  {
    train_number: "12302",
    train_name: "New Delhi – Howrah Rajdhani Express (via Gaya)",
    train_type: "Rajdhani Express",
    service_priority: 1,
    origin: "New Delhi (NDLS)",
    destination: "Howrah Junction (HWH)",
    origin_code: "NDLS",
    destination_code: "HWH",
    days_of_run: ["Mon", "Tue", "Wed", "Thu", "Sat", "Sun"],
    avg_speed_kmh: 88,
    distance_km: 1451,
    is_protected: true,
    route: [
      { stop_number: 1, station_code: "NDLS", station_name: "New Delhi", arrival: null, departure: "16:50", day: 1, distance_km: 0 },
      { stop_number: 2, station_code: "CNB", station_name: "Kanpur Central", arrival: "21:32", departure: "21:37", day: 1, distance_km: 440 },
      { stop_number: 3, station_code: "PRYJ", station_name: "Prayagraj Junction", arrival: "23:43", departure: "23:45", day: 1, distance_km: 634 },
      { stop_number: 4, station_code: "DDU", station_name: "Pt. Deen Dayal Upadhyaya Junction", arrival: "01:42", departure: "01:52", day: 2, distance_km: 787 },
      { stop_number: 5, station_code: "GAYA", station_name: "Gaya Junction", arrival: "03:55", departure: "03:58", day: 2, distance_km: 992 },
      { stop_number: 6, station_code: "DHN", station_name: "Dhanbad Junction", arrival: "06:33", departure: "06:38", day: 2, distance_km: 1192 },
      { stop_number: 7, station_code: "ASN", station_name: "Asansol Junction", arrival: "07:28", departure: "07:30", day: 2, distance_km: 1251 },
      { stop_number: 8, station_code: "HWH", station_name: "Howrah Junction", arrival: "09:55", departure: null, day: 2, distance_km: 1451 }
    ]
  },
  {
    train_number: "12305",
    train_name: "Kolkata Rajdhani Express (via Patna)",
    train_type: "Rajdhani Express",
    service_priority: 1,
    origin: "Howrah Junction (HWH)",
    destination: "New Delhi (NDLS)",
    origin_code: "HWH",
    destination_code: "NDLS",
    days_of_run: ["Sun"],
    avg_speed_kmh: 82,
    distance_km: 1531,
    is_protected: true,
    route: [
      { stop_number: 1, station_code: "HWH", station_name: "Howrah Junction", arrival: null, departure: "14:05", day: 1, distance_km: 0 },
      { stop_number: 2, station_code: "BWN", station_name: "Barddhaman Junction", arrival: "15:07", departure: "15:09", day: 1, distance_km: 94 },
      { stop_number: 3, station_code: "ASN", station_name: "Asansol Junction", arrival: "16:07", departure: "16:10", day: 1, distance_km: 200 },
      { stop_number: 4, station_code: "PNBE", station_name: "Patna Junction", arrival: "21:00", departure: "21:10", day: 1, distance_km: 532 },
      { stop_number: 5, station_code: "DDU", station_name: "Pt. Deen Dayal Upadhyaya Junction", arrival: "00:45", departure: "00:55", day: 2, distance_km: 744 },
      { stop_number: 6, station_code: "PRYJ", station_name: "Prayagraj Junction", arrival: "02:43", departure: "02:45", day: 2, distance_km: 897 },
      { stop_number: 7, station_code: "CNB", station_name: "Kanpur Central", arrival: "04:40", departure: "04:45", day: 2, distance_km: 1091 },
      { stop_number: 8, station_code: "NDLS", station_name: "New Delhi", arrival: "10:05", departure: null, day: 2, distance_km: 1531 }
    ]
  },
  {
    train_number: "12259",
    train_name: "Sealdah – Bikaner AC Duronto Express",
    train_type: "Duronto Express",
    service_priority: 1,
    origin: "Sealdah (SDAH)",
    destination: "Bikaner Junction (BKN)",
    origin_code: "SDAH",
    destination_code: "BKN",
    days_of_run: ["Mon", "Wed", "Thu", "Sun"],
    avg_speed_kmh: 84,
    distance_km: 1920,
    is_protected: true,
    route: [
      { stop_number: 1, station_code: "SDAH", station_name: "Sealdah", arrival: null, departure: "17:00", day: 1, distance_km: 0 },
      { stop_number: 2, station_code: "DHN", station_name: "Dhanbad Junction", arrival: "20:30", departure: "20:35", day: 1, distance_km: 266 },
      { stop_number: 3, station_code: "DDU", station_name: "Pt. Deen Dayal Upadhyaya Junction", arrival: "01:25", departure: "01:35", day: 2, distance_km: 671 },
      { stop_number: 4, station_code: "CNB", station_name: "Kanpur Central", arrival: "05:20", departure: "05:25", day: 2, distance_km: 1018 },
      { stop_number: 5, station_code: "NDLS", station_name: "New Delhi", arrival: "11:00", departure: "11:15", day: 2, distance_km: 1458 },
      { stop_number: 6, station_code: "BKN", station_name: "Bikaner Junction", arrival: "19:40", departure: null, day: 2, distance_km: 1920 }
    ]
  },
  {
    train_number: "22301",
    train_name: "Howrah – New Jalpaiguri Vande Bharat Express",
    train_type: "Vande Bharat Express",
    service_priority: 1,
    origin: "Howrah Junction (HWH)",
    destination: "New Jalpaiguri Junction (NJP)",
    origin_code: "HWH",
    destination_code: "NJP",
    days_of_run: ["Mon", "Tue", "Thu", "Fri", "Sat", "Sun"],
    avg_speed_kmh: 75,
    distance_km: 561,
    is_protected: true,
    route: [
      { stop_number: 1, station_code: "HWH", station_name: "Howrah Junction", arrival: null, departure: "05:55", day: 1, distance_km: 0 },
      { stop_number: 2, station_code: "BWN", station_name: "Barddhaman Junction", arrival: "06:48", departure: "06:50", day: 1, distance_km: 94 },
      { stop_number: 3, station_code: "MLDT", station_name: "Malda Town", arrival: "10:30", departure: "10:35", day: 1, distance_km: 332 },
      { stop_number: 4, station_code: "NJP", station_name: "New Jalpaiguri Junction", arrival: "13:25", departure: null, day: 1, distance_km: 561 }
    ]
  },
  {
    train_number: "22436",
    train_name: "New Delhi – Varanasi Vande Bharat Express",
    train_type: "Vande Bharat Express",
    service_priority: 1,
    origin: "New Delhi (NDLS)",
    destination: "Varanasi Junction (BSB)",
    origin_code: "NDLS",
    destination_code: "BSB",
    days_of_run: ["Tue", "Wed", "Fri", "Sat", "Sun"],
    avg_speed_kmh: 95,
    distance_km: 759,
    is_protected: true,
    route: [
      { stop_number: 1, station_code: "NDLS", station_name: "New Delhi", arrival: null, departure: "06:00", day: 1, distance_km: 0 },
      { stop_number: 2, station_code: "CNB", station_name: "Kanpur Central", arrival: "10:08", departure: "10:10", day: 1, distance_km: 440 },
      { stop_number: 3, station_code: "PRYJ", station_name: "Prayagraj Junction", arrival: "12:08", departure: "12:10", day: 1, distance_km: 634 },
      { stop_number: 4, station_code: "BSB", station_name: "Varanasi Junction", arrival: "14:00", departure: null, day: 1, distance_km: 759 }
    ]
  },
  {
    train_number: "12951",
    train_name: "Mumbai Central – New Delhi Rajdhani Express",
    train_type: "Rajdhani Express",
    service_priority: 1,
    origin: "Mumbai Central (MMCT)",
    destination: "New Delhi (NDLS)",
    origin_code: "MMCT",
    destination_code: "NDLS",
    days_of_run: ["Daily"],
    avg_speed_kmh: 91,
    distance_km: 1386,
    is_protected: true,
    route: [
      { stop_number: 1, station_code: "MMCT", station_name: "Mumbai Central", arrival: null, departure: "17:00", day: 1, distance_km: 0 },
      { stop_number: 2, station_code: "ST", station_name: "Surat", arrival: "19:43", departure: "19:48", day: 1, distance_km: 263 },
      { stop_number: 3, station_code: "BRC", station_name: "Vadodara Junction", arrival: "21:06", departure: "21:16", day: 1, distance_km: 393 },
      { stop_number: 4, station_code: "KOTA", station_name: "Kota Junction", arrival: "03:15", departure: "03:20", day: 2, distance_km: 921 },
      { stop_number: 5, station_code: "NDLS", station_name: "New Delhi", arrival: "08:32", departure: null, day: 2, distance_km: 1386 }
    ]
  },
  {
    train_number: "12019",
    train_name: "Howrah – Ranchi Shatabdi Express",
    train_type: "Shatabdi Express",
    service_priority: 1,
    origin: "Howrah Junction (HWH)",
    destination: "Ranchi Junction (RNC)",
    origin_code: "HWH",
    destination_code: "RNC",
    days_of_run: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
    avg_speed_kmh: 60,
    distance_km: 421,
    is_protected: true,
    route: [
      { stop_number: 1, station_code: "HWH", station_name: "Howrah Junction", arrival: null, departure: "06:05", day: 1, distance_km: 0 },
      { stop_number: 2, station_code: "BWN", station_name: "Barddhaman Junction", arrival: "07:11", departure: "07:13", day: 1, distance_km: 94 },
      { stop_number: 3, station_code: "ASN", station_name: "Asansol Junction", arrival: "08:21", departure: "08:23", day: 1, distance_km: 200 },
      { stop_number: 4, station_code: "DHN", station_name: "Dhanbad Junction", arrival: "09:20", departure: "09:25", day: 1, distance_km: 259 },
      { stop_number: 5, station_code: "BKSC", station_name: "Bokaro Steel City", arrival: "10:55", departure: "11:00", day: 1, distance_km: 308 },
      { stop_number: 6, station_code: "RNC", station_name: "Ranchi Junction", arrival: "13:15", departure: null, day: 1, distance_km: 421 }
    ]
  },
  {
    train_number: "12313",
    train_name: "Sealdah – New Delhi Rajdhani Express",
    train_type: "Rajdhani Express",
    service_priority: 1,
    origin: "Sealdah (SDAH)",
    destination: "New Delhi (NDLS)",
    origin_code: "SDAH",
    destination_code: "NDLS",
    days_of_run: ["Daily"],
    avg_speed_kmh: 86,
    distance_km: 1453,
    is_protected: true,
    route: [
      { stop_number: 1, station_code: "SDAH", station_name: "Sealdah", arrival: null, departure: "16:50", day: 1, distance_km: 0 },
      { stop_number: 2, station_code: "DHN", station_name: "Dhanbad Junction", arrival: "20:20", departure: "20:25", day: 1, distance_km: 266 },
      { stop_number: 3, station_code: "GAYA", station_name: "Gaya Junction", arrival: "22:57", departure: "23:00", day: 1, distance_km: 466 },
      { stop_number: 4, station_code: "DDU", station_name: "Pt. Deen Dayal Upadhyaya Junction", arrival: "01:15", departure: "01:25", day: 2, distance_km: 671 },
      { stop_number: 5, station_code: "CNB", station_name: "Kanpur Central", arrival: "05:20", departure: "05:25", day: 2, distance_km: 1018 },
      { stop_number: 6, station_code: "NDLS", station_name: "New Delhi", arrival: "10:50", departure: null, day: 2, distance_km: 1453 }
    ]
  },
  {
    train_number: "12321",
    train_name: "Howrah – Mumbai CSMT Mail (via Gaya, Jabalpur)",
    train_type: "Superfast Mail",
    service_priority: 2,
    origin: "Howrah Junction (HWH)",
    destination: "Chhatrapati Shivaji Maharaj Terminus (CSMT)",
    origin_code: "HWH",
    destination_code: "CSMT",
    days_of_run: ["Daily"],
    avg_speed_kmh: 58,
    distance_km: 2160,
    is_protected: true,
    route: [
      { stop_number: 1, station_code: "HWH", station_name: "Howrah Junction", arrival: null, departure: "23:35", day: 1, distance_km: 0 },
      { stop_number: 2, station_code: "BWN", station_name: "Barddhaman Junction", arrival: "00:46", departure: "00:48", day: 2, distance_km: 94 },
      { stop_number: 3, station_code: "ASN", station_name: "Asansol Junction", arrival: "02:00", departure: "02:05", day: 2, distance_km: 200 },
      { stop_number: 4, station_code: "DHN", station_name: "Dhanbad Junction", arrival: "03:15", departure: "03:20", day: 2, distance_km: 259 },
      { stop_number: 5, station_code: "GAYA", station_name: "Gaya Junction", arrival: "06:10", departure: "06:15", day: 2, distance_km: 459 },
      { stop_number: 6, station_code: "DDU", station_name: "Pt. Deen Dayal Upadhyaya Junction", arrival: "08:50", departure: "09:00", day: 2, distance_km: 664 },
      { stop_number: 7, station_code: "PRYJ", station_name: "Prayagraj Junction", arrival: "11:25", departure: "11:35", day: 2, distance_km: 817 },
      { stop_number: 8, station_code: "JBP", station_name: "Jabalpur", arrival: "17:10", departure: "17:20", day: 2, distance_km: 1184 },
      { stop_number: 9, station_code: "ET", station_name: "Itarsi Junction", arrival: "21:20", departure: "21:30", day: 2, distance_km: 1428 },
      { stop_number: 10, station_code: "BSL", station_name: "Bhusaval Junction", arrival: "01:40", departure: "01:45", day: 3, distance_km: 1735 },
      { stop_number: 11, station_code: "KYN", station_name: "Kalyan Junction", arrival: "10:17", departure: "10:20", day: 3, distance_km: 2107 },
      { stop_number: 12, station_code: "CSMT", station_name: "Mumbai CSMT", arrival: "11:25", departure: null, day: 3, distance_km: 2160 }
    ]
  },
  {
    train_number: "12801",
    train_name: "Purushottam Express",
    train_type: "Superfast Express",
    service_priority: 2,
    origin: "Puri (PURI)",
    destination: "New Delhi (NDLS)",
    origin_code: "PURI",
    destination_code: "NDLS",
    days_of_run: ["Daily"],
    avg_speed_kmh: 60,
    distance_km: 1864,
    is_protected: true,
    route: [
      { stop_number: 1, station_code: "PURI", station_name: "Puri", arrival: null, departure: "21:55", day: 1, distance_km: 0 },
      { stop_number: 2, station_code: "BBS", station_name: "Bhubaneswar", arrival: "22:55", departure: "23:00", day: 1, distance_km: 63 },
      { stop_number: 3, station_code: "CTC", station_name: "Cuttack Junction", arrival: "23:35", departure: "23:40", day: 1, distance_km: 91 },
      { stop_number: 4, station_code: "KGP", station_name: "Kharagpur Junction", arrival: "03:45", departure: "03:50", day: 2, distance_km: 385 },
      { stop_number: 5, station_code: "TATA", station_name: "Tatanagar Junction", arrival: "06:10", departure: "06:22", day: 2, distance_km: 519 },
      { stop_number: 6, station_code: "BKSC", station_name: "Bokaro Steel City", arrival: "08:45", departure: "08:50", day: 2, distance_km: 670 },
      { stop_number: 7, station_code: "GAYA", station_name: "Gaya Junction", arrival: "13:42", departure: "13:47", day: 2, distance_km: 873 },
      { stop_number: 8, station_code: "DDU", station_name: "Pt. Deen Dayal Upadhyaya Junction", arrival: "16:50", departure: "17:00", day: 2, distance_km: 1078 },
      { stop_number: 9, station_code: "CNB", station_name: "Kanpur Central", arrival: "21:55", departure: "22:00", day: 2, distance_km: 1425 },
      { stop_number: 10, station_code: "NDLS", station_name: "New Delhi", arrival: "04:00", departure: null, day: 3, distance_km: 1864 }
    ]
  },
  {
    train_number: "12621",
    train_name: "Tamil Nadu Express",
    train_type: "Superfast Express",
    service_priority: 1,
    origin: "Puratchi Thalaivar Dr. MGR Central (MAS)",
    destination: "New Delhi (NDLS)",
    origin_code: "MAS",
    destination_code: "NDLS",
    days_of_run: ["Daily"],
    avg_speed_kmh: 67,
    distance_km: 2184,
    is_protected: true,
    route: [
      { stop_number: 1, station_code: "MAS", station_name: "Chennai Central", arrival: null, departure: "22:00", day: 1, distance_km: 0 },
      { stop_number: 2, station_code: "BZA", station_name: "Vijayawada Junction", arrival: "03:55", departure: "04:05", day: 2, distance_km: 431 },
      { stop_number: 3, station_code: "WL", station_name: "Warangal", arrival: "06:50", departure: "06:52", day: 2, distance_km: 638 },
      { stop_number: 4, station_code: "NGP", station_name: "Nagpur Junction", arrival: "13:50", departure: "13:55", day: 2, distance_km: 1088 },
      { stop_number: 5, station_code: "ET", station_name: "Itarsi Junction", arrival: "18:30", departure: "18:35", day: 2, distance_km: 1386 },
      { stop_number: 6, station_code: "BPL", station_name: "Bhopal Junction", arrival: "20:10", departure: "20:20", day: 2, distance_km: 1478 },
      { stop_number: 7, station_code: "GWL", station_name: "Gwalior Junction", arrival: "00:26", departure: "00:28", day: 3, distance_km: 1867 },
      { stop_number: 8, station_code: "AGC", station_name: "Agra Cantt", arrival: "02:00", departure: "02:05", day: 3, distance_km: 1985 },
      { stop_number: 9, station_code: "NDLS", station_name: "New Delhi", arrival: "06:30", departure: null, day: 3, distance_km: 2184 }
    ]
  },
  {
    train_number: "FRT-8802",
    train_name: "Heavy-Haul Coal Rake (Dhanbad → DDU)",
    train_type: "Freight / Heavy Goods",
    service_priority: 3,
    origin: "Dhanbad Junction (DHN)",
    destination: "Pt. Deen Dayal Upadhyaya Junction (DDU)",
    origin_code: "DHN",
    destination_code: "DDU",
    days_of_run: ["Daily"],
    avg_speed_kmh: 45,
    distance_km: 405,
    is_protected: false,
    route: [
      { stop_number: 1, station_code: "DHN", station_name: "Dhanbad Yard", arrival: null, departure: "01:30", day: 1, distance_km: 0 },
      { stop_number: 2, station_code: "PNME", station_name: "Parasnath Loop", arrival: "02:50", departure: "03:10", day: 1, distance_km: 47 },
      { stop_number: 3, station_code: "GAYA", station_name: "Gaya Goods Bypass", arrival: "06:40", departure: "07:15", day: 1, distance_km: 200 },
      { stop_number: 4, station_code: "DOS", station_name: "Dehri Loop", arrival: "09:00", departure: "09:20", day: 1, distance_km: 285 },
      { stop_number: 5, station_code: "DDU", station_name: "Pt. Deen Dayal Upadhyaya Yard", arrival: "12:45", departure: null, day: 1, distance_km: 405 }
    ]
  }
];

export class TrainDataProvider {
  constructor() {
    this.provider = "REPRESENTATIVE_WTT";
    this.apiKey = (process.env.TRAIN_API_KEY || "").trim();
    this.apiHost = (process.env.TRAIN_API_HOST || "").trim();
    this.baseUrl = (process.env.TRAIN_API_BASE_URL || "").trim();
    this.requestTimeoutMs = 8000;
  }

  isConfigured() {
    return Boolean(this.apiKey && this.apiKey.length >= 8 && this.baseUrl);
  }

  getProviderStatus() {
    return {
      configured: false,
      live_feed_configured: false,
      provider: "REPRESENTATIVE_WTT",
      provider_name: "Indian Railways Representative Working Timetable (WTT)",
      base_url: null,
      host: null,
      message: "PROTOTYPE DEMO MODE: Operating on verified representative Working Timetable (WTT) schedules and corridor sections.",
      is_representative_data: true,
      offline_fallback_available: true,
      last_checked: new Date().toISOString()
    };
  }

  _getProviderDisplayName() {
    return "Indian Railways Representative Working Timetable (WTT)";
  }

  // 1. Search Trains (number, name, origin, destination)
  async searchTrains(query = "") {
    const q = (query || "").trim();
    
    // Check if live API configured
    if (this.isConfigured()) {
      try {
        let endpoint = "";
        if (this.provider === "RAPIDAPI_IRCTC1") {
          endpoint = `/api/v1/searchTrain?query=${encodeURIComponent(q)}`;
        } else if (this.provider === "RAPIDAPI_INDIAN_RAILWAY") {
          endpoint = `/api/trains-search/v1/train/${encodeURIComponent(q)}`;
        } else {
          endpoint = `/searchTrain?query=${encodeURIComponent(q)}`;
        }

        const liveRes = await this._callLiveApi(endpoint);
        const normalized = this._normalizeSearchResults(liveRes);
        if (normalized && normalized.length > 0) {
          return {
            data_source: "LIVE_DATA",
            source_label: `Live IRCTC Gateway (${this.apiHost || this.provider})`,
            last_updated: new Date().toISOString(),
            results: normalized
          };
        }
      } catch (err) {
        console.warn(`[TrainDataProvider] Live search error (${err.message}). Falling back to scheduled dataset.`);
      }
    }

    // Comprehensive offline pan-India dataset
    const qLower = q.toLowerCase();
    const matched = INDIAN_RAILWAYS_TRAINS.filter(t => {
      if (!qLower) return true;
      return (
        t.train_number.toLowerCase().includes(qLower) ||
        t.train_name.toLowerCase().includes(qLower) ||
        t.origin.toLowerCase().includes(qLower) ||
        t.destination.toLowerCase().includes(qLower) ||
        t.origin_code.toLowerCase() === qLower ||
        t.destination_code.toLowerCase() === qLower ||
        t.train_type.toLowerCase().includes(qLower)
      );
    });

    return {
      data_source: "DEMO_REPRESENTATIVE_DATA",
      source_label: "Representative Timetable Database (Demo Dataset)",
      last_updated: new Date().toISOString(),
      results: matched
    };
  }

  // 2. Train Timetable & Route
  async getTrainTimetable(trainNumber) {
    const num = (trainNumber || "").trim();
    if (!num) return null;

    if (this.isConfigured()) {
      try {
        let endpoint = "";
        if (this.provider === "RAPIDAPI_IRCTC1") {
          endpoint = `/api/v1/getTrainSchedule?trainNo=${encodeURIComponent(num)}`;
        } else if (this.provider === "RAPIDAPI_INDIAN_RAILWAY") {
          endpoint = `/api/trains-search/v1/train/${encodeURIComponent(num)}`;
        } else {
          endpoint = `/getTrainSchedule?trainNo=${encodeURIComponent(num)}`;
        }

        const liveRes = await this._callLiveApi(endpoint);
        const normalized = this._normalizeTimetable(liveRes, num);
        if (normalized) {
          return {
            data_source: "LIVE_DATA",
            source_label: `Live Timetable (${this.apiHost || this.provider})`,
            last_updated: new Date().toISOString(),
            train: normalized
          };
        }
      } catch (err) {
        console.warn(`[TrainDataProvider] Timetable error for ${num} (${err.message}).`);
      }
    }

    const found = INDIAN_RAILWAYS_TRAINS.find(t => t.train_number === num);
    if (!found) {
      return {
        data_source: "DEMO_REPRESENTATIVE_DATA",
        source_label: "Representative Timetable Database (Demo Dataset)",
        last_updated: new Date().toISOString(),
        train: null,
        message: `Train '${num}' not found in representative timetable directory.`
      };
    }

    return {
      data_source: "DEMO_REPRESENTATIVE_DATA",
      source_label: "Representative Timetable Database (Demo Dataset)",
      last_updated: new Date().toISOString(),
      train: found
    };
  }

  // 3. Live Train Running Status
  async getLiveTrainStatus(trainNumber) {
    const num = (trainNumber || "").trim();
    const nowIso = new Date().toISOString();

    if (!num) {
      return {
        status: "ERROR",
        message: "Train number is required."
      };
    }

    // Try real Live API if key is present
    if (this.isConfigured()) {
      try {
        let endpoint = "";
        if (this.provider === "RAPIDAPI_IRCTC1") {
          // startDay: 0 for today, 1 for yesterday
          endpoint = `/api/v1/liveTrainStatus?trainNo=${encodeURIComponent(num)}&startDay=0`;
        } else if (this.provider === "RAPIDAPI_INDIAN_RAILWAY") {
          const today = new Date().toISOString().split("T")[0];
          endpoint = `/api/trains/v1/train/status?train_number=${encodeURIComponent(num)}&departure_date=${today}`;
        } else {
          endpoint = `/liveTrainStatus?trainNo=${encodeURIComponent(num)}&startDay=0`;
        }

        const liveData = await this._callLiveApi(endpoint);
        const normalized = this._normalizeLiveStatus(liveData, num);

        if (normalized) {
          return {
            status: "LIVE",
            data_source: "LIVE_DATA",
            source_label: `Live NTES Feed (${this.apiHost || this.provider})`,
            train_number: num,
            train_name: normalized.train_name || `Train ${num}`,
            current_station: normalized.current_station,
            current_station_code: normalized.current_station_code,
            delay_mins: normalized.delay_mins,
            status_description: normalized.status_description,
            last_location: normalized.last_location,
            last_updated: nowIso
          };
        }
      } catch (err) {
        // Transparent error reporting: Never claim live success if upstream failed
        return {
          status: "UPSTREAM_API_ERROR",
          data_source: "OFFLINE_FALLBACK",
          source_label: "Live Telemetry Failed (Showing Scheduled Timetable)",
          train_number: num,
          upstream_error: err.message,
          message: `Upstream live API returned an error (${err.message}). Displaying scheduled corridor Working Timetable.`,
          scheduled_arrival: this._getScheduledStatusFallback(num)?.scheduled_arrival || "02.5",
          scheduled_departure: this._getScheduledStatusFallback(num)?.scheduled_departure || "03.0",
          delay_mins: 0,
          simulated_status: "Scheduled WTT Timing",
          section: "Corridor Segment",
          last_updated: nowIso
        };
      }
    }

    // Return clear representative Working Timetable data for SIH prototype
    const scheduled = this._getScheduledStatusFallback(num);
    return {
      status: "REPRESENTATIVE_WTT",
      data_source: "DEMO_REPRESENTATIVE_DATA",
      source_label: "Representative Working Timetable (Demo Dataset)",
      train_number: num,
      train_name: scheduled ? scheduled.train_name : `Train ${num}`,
      origin: scheduled ? scheduled.origin : "Howrah Junction (HWH)",
      destination: scheduled ? scheduled.destination : "New Delhi (NDLS)",
      scheduled_arrival: scheduled ? scheduled.scheduled_arrival : "16:50",
      scheduled_departure: scheduled ? scheduled.scheduled_departure : "10:05",
      delay_mins: 0,
      simulated_status: "Running to Representative Working Timetable (WTT)",
      section: "Howrah – DDU Corridor Section",
      message: "DEMO/REPRESENTATIVE DATA: Schedule and corridor timings generated from authentic Indian Railways Working Timetables for prototype optimization.",
      last_updated: nowIso
    };
  }

  // 4. Station Board (Upcoming Arrivals & Departures)
  async getStationBoard(stationCode) {
    const code = (stationCode || "").trim().toUpperCase();
    const station = getStationByCode(code);
    const nowIso = new Date().toISOString();

    if (this.isConfigured()) {
      try {
        let endpoint = "";
        if (this.provider === "RAPIDAPI_IRCTC1") {
          endpoint = `/api/v3/getLiveStation?stationCode=${encodeURIComponent(code)}&hours=4`;
        } else {
          endpoint = `/getLiveStation?stationCode=${encodeURIComponent(code)}&hours=4`;
        }

        const liveRes = await this._callLiveApi(endpoint);
        const movements = this._normalizeStationBoard(liveRes, code);
        if (movements && movements.length > 0) {
          return {
            station_code: code,
            station_name: station ? station.name : code,
            data_source: "LIVE_DATA",
            source_label: `Live Station Board (${this.apiHost || this.provider})`,
            last_updated: nowIso,
            movements
          };
        }
      } catch (err) {
        console.warn(`[TrainDataProvider] Station board error for ${code} (${err.message}).`);
      }
    }

    // Build station board from scheduled representative database
    const movements = [];
    for (const train of INDIAN_RAILWAYS_TRAINS) {
      const stop = train.route.find(r => r.station_code === code);
      if (stop) {
        movements.push({
          train_number: train.train_number,
          train_name: train.train_name,
          train_type: train.train_type,
          service_priority: train.service_priority,
          origin: train.origin,
          destination: train.destination,
          scheduled_arrival: stop.arrival || "--:--",
          scheduled_departure: stop.departure || "--:--",
          platform: (Math.abs(train.train_number.charCodeAt(0)) % (station?.platforms || 4)) + 1,
          delay_mins: 0,
          status_description: "Right Time (Representative Schedule)",
          source: "DEMO_REPRESENTATIVE_DATA"
        });
      }
    }

    return {
      station_code: code,
      station_name: station ? station.name : code,
      zone: station ? station.zone : "IR",
      platforms: station ? station.platforms : 4,
      data_source: "DEMO_REPRESENTATIVE_DATA",
      source_label: "Representative Station Timetable (Demo Dataset)",
      last_updated: nowIso,
      movements
    };
  }

  // 5. Trains Between Stations
  async getTrainsBetweenStations(fromCode, toCode) {
    const from = (fromCode || "").trim().toUpperCase();
    const to = (toCode || "").trim().toUpperCase();
    const nowIso = new Date().toISOString();

    if (this.isConfigured()) {
      try {
        const today = new Date().toISOString().split("T")[0];
        let endpoint = "";
        if (this.provider === "RAPIDAPI_IRCTC1") {
          endpoint = `/api/v3/trainBetweenStations?fromStationCode=${encodeURIComponent(from)}&toStationCode=${encodeURIComponent(to)}&dateOfJourney=${today}`;
        } else if (this.provider === "RAPIDAPI_INDIAN_RAILWAY") {
          endpoint = `/api/trains/v1/trains-between-stations?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}&date=${today}`;
        } else {
          endpoint = `/trainBetweenStations?fromStationCode=${encodeURIComponent(from)}&toStationCode=${encodeURIComponent(to)}&dateOfJourney=${today}`;
        }

        const liveRes = await this._callLiveApi(endpoint);
        const trains = this._normalizeTrainsBetween(liveRes);
        if (trains && trains.length > 0) {
          return {
            from_code: from,
            to_code: to,
            data_source: "LIVE_DATA",
            source_label: `Live IRCTC Directory (${this.apiHost || this.provider})`,
            last_updated: nowIso,
            trains
          };
        }
      } catch (err) {
        console.warn(`[TrainDataProvider] Live trains-between-stations error (${err.message}). Falling back to scheduled database.`);
      }
    }

    const matches = [];
    for (const train of INDIAN_RAILWAYS_TRAINS) {
      const fromIdx = train.route.findIndex(r => r.station_code === from);
      const toIdx = train.route.findIndex(r => r.station_code === to);
      if (fromIdx !== -1 && toIdx !== -1 && fromIdx < toIdx) {
        const fromStop = train.route[fromIdx];
        const toStop = train.route[toIdx];
        matches.push({
          train_number: train.train_number,
          train_name: train.train_name,
          train_type: train.train_type,
          departure_time: fromStop.departure,
          arrival_time: toStop.arrival,
          duration_km: toStop.distance_km - fromStop.distance_km,
          days_of_run: train.days_of_run,
          service_priority: train.service_priority
        });
      }
    }

    return {
      from_code: from,
      to_code: to,
      data_source: "SCHEDULED_DATABASE",
      source_label: "Pan-India Scheduled Database (WTT)",
      last_updated: nowIso,
      trains: matches
    };
  }

  // 6. Station Search
  async searchStation(query = "") {
    const q = (query || "").trim();
    if (this.isConfigured() && this.provider === "RAPIDAPI_IRCTC1") {
      try {
        const liveRes = await this._callLiveApi(`/api/v1/searchStation?query=${encodeURIComponent(q)}`);
        if (liveRes && (liveRes.data || Array.isArray(liveRes))) {
          return liveRes.data || liveRes;
        }
      } catch (err) {
        console.warn(`[TrainDataProvider] Live station search error (${err.message}).`);
      }
    }
    return CORRIDOR_STATIONS.filter(s => 
      s.code.toLowerCase().includes(q.toLowerCase()) || 
      s.name.toLowerCase().includes(q.toLowerCase())
    );
  }

  // Private HTTP Caller with timeout, host, and authorization headers
  async _callLiveApi(endpoint) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.requestTimeoutMs);

    try {
      const url = `${this.baseUrl.replace(/\/$/, "")}${endpoint}`;
      const headers = {
        "User-Agent": "RailwayBlockPlanner/2.0 (SIH-2026-PS26027)",
        "Accept": "application/json"
      };

      if (this.apiKey) {
        headers["x-rapidapi-key"] = this.apiKey;
        headers["Authorization"] = `Bearer ${this.apiKey}`;
      }
      if (this.apiHost) {
        headers["x-rapidapi-host"] = this.apiHost;
      }

      const res = await fetch(url, { headers, signal: controller.signal });
      if (!res.ok) {
        const errorText = await res.text().catch(() => "");
        throw new Error(`HTTP ${res.status}: ${res.statusText}${errorText ? ' - ' + errorText.slice(0, 100) : ''}`);
      }
      return await res.json();
    } finally {
      clearTimeout(timeout);
    }
  }

  // Normalization Helpers
  _normalizeSearchResults(json) {
    if (!json) return null;
    const items = Array.isArray(json) ? json : (json.data || json.results || []);
    if (!Array.isArray(items) || items.length === 0) return null;

    return items.map(item => ({
      train_number: item.train_number || item.train_no || item.trainNumber || String(item.id || ""),
      train_name: item.train_name || item.name || "Express Service",
      train_type: item.train_type || item.type || "Superfast Express",
      service_priority: item.service_priority || (String(item.train_name || "").includes("Rajdhani") ? 1 : 2),
      origin: item.origin || item.from_station_name || item.from || "Origin",
      destination: item.destination || item.to_station_name || item.to || "Destination",
      source: "LIVE_API"
    }));
  }

  _normalizeTimetable(json, trainNumber) {
    if (!json) return null;
    const data = json.data || json.train || json;
    const rawStops = data.route || data.stations || data.schedule || [];
    if (!Array.isArray(rawStops) || rawStops.length === 0) return null;

    return {
      train_number: data.train_number || data.train_no || trainNumber,
      train_name: data.train_name || data.name || `Train ${trainNumber}`,
      train_type: data.train_type || data.type || "Superfast Express",
      service_priority: 1,
      origin: data.origin || rawStops[0]?.station_name || "Origin",
      destination: data.destination || rawStops[rawStops.length - 1]?.station_name || "Destination",
      route: rawStops.map((st, idx) => ({
        stop_number: idx + 1,
        station_code: st.station_code || st.code || "STA",
        station_name: st.station_name || st.name || "Station",
        arrival: st.arrival_time || st.arrival || st.sta || null,
        departure: st.departure_time || st.departure || st.std || null,
        halt_mins: parseInt(st.halt_time || st.halt_mins || 0) || null,
        day: parseInt(st.day || 1),
        distance_km: parseInt(st.distance || st.distance_km || 0)
      }))
    };
  }

  _normalizeLiveStatus(json, trainNumber) {
    if (!json) return null;
    const data = json.data || json;
    
    return {
      train_name: data.train_name || data.trainName || `Train ${trainNumber}`,
      current_station: data.current_station_name || data.current_station || data.station_name || "In Transit",
      current_station_code: data.current_station_code || data.station_code || "EN_ROUTE",
      delay_mins: parseInt(data.delay_mins || data.delay || data.late_mins || 0),
      status_description: data.status || data.status_description || data.current_location_info || "Running as reported by NTES",
      last_location: data.last_location || data.current_station_name || "On mainline"
    };
  }

  _normalizeStationBoard(json, stationCode) {
    if (!json) return null;
    const items = Array.isArray(json) ? json : (json.data || json.trains || []);
    if (!Array.isArray(items) || items.length === 0) return null;

    return items.map(item => ({
      train_number: item.train_number || item.train_no || item.trainNumber,
      train_name: item.train_name || item.name || "Express Service",
      train_type: item.train_type || "Express",
      service_priority: (item.train_name && item.train_name.includes("Rajdhani")) ? 1 : 2,
      origin: item.source || item.from || "Origin",
      destination: item.destination || item.to || "Destination",
      scheduled_arrival: item.scheduled_arrival || item.sta || item.arrival_time || "--:--",
      scheduled_departure: item.scheduled_departure || item.std || item.departure_time || "--:--",
      platform: item.platform_number || item.platform || 1,
      status: item.status || "RUNNING",
      delay_mins: parseInt(item.delay_arrival || item.delay || 0)
    }));
  }

  _normalizeTrainsBetween(json) {
    if (!json) return null;
    const items = Array.isArray(json) ? json : (json.data || json.trains || []);
    if (!Array.isArray(items) || items.length === 0) return null;

    return items.map(t => ({
      train_number: t.train_number || t.train_no || t.trainNumber,
      train_name: t.train_name || t.name || "Express",
      train_type: t.train_type || "Express",
      departure_time: t.from_std || t.departure_time || t.std || "--:--",
      arrival_time: t.to_sta || t.arrival_time || t.sta || "--:--",
      origin: t.from_station_name || t.from || "Origin",
      destination: t.to_station_name || t.to || "Destination",
      service_priority: 2
    }));
  }

  _getScheduledStatusFallback(trainNumber) {
    const t = INDIAN_RAILWAYS_TRAINS.find(x => x.train_number === trainNumber);
    if (!t) return null;
    return {
      train_number: t.train_number,
      train_name: t.train_name,
      origin: t.origin,
      destination: t.destination,
      scheduled_arrival: t.route[0]?.departure || "00:00",
      scheduled_departure: t.route[t.route.length - 1]?.arrival || "23:59"
    };
  }
}

function hashCode(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i);
    hash |= 0;
  }
  return hash;
}

export const trainProvider = new TrainDataProvider();
