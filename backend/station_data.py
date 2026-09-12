from typing import List, Dict, Any, Optional

# Comprehensive curated Indian Railways Station Directory
# Covering major junctions across all Indian States & Zones
STATIONS_DB: List[Dict[str, Any]] = [
    # West Bengal (Eastern Railway / South Eastern Railway)
    {"code": "HWH", "name": "Howrah Junction", "city": "Kolkata", "district": "Howrah", "state": "West Bengal", "zone": "ER", "lat": 22.5838, "lng": 88.3426, "platforms": 23},
    {"code": "SDAH", "name": "Sealdah", "city": "Kolkata", "district": "Kolkata", "state": "West Bengal", "zone": "ER", "lat": 22.5683, "lng": 88.3712, "platforms": 21},
    {"code": "KOAA", "name": "Kolkata Terminal", "city": "Kolkata", "district": "Kolkata", "state": "West Bengal", "zone": "ER", "lat": 22.6025, "lng": 88.3769, "platforms": 5},
    {"code": "BWN", "name": "Barddhaman Junction", "city": "Bardhaman", "district": "Purba Bardhaman", "state": "West Bengal", "zone": "ER", "lat": 23.2324, "lng": 87.8615, "platforms": 8},
    {"code": "ASN", "name": "Asansol Junction", "city": "Asansol", "district": "Paschim Bardhaman", "state": "West Bengal", "zone": "ER", "lat": 23.6871, "lng": 86.9746, "platforms": 7},
    {"code": "KGP", "name": "Kharagpur Junction", "city": "Kharagpur", "district": "Paschim Medinipur", "state": "West Bengal", "zone": "SER", "lat": 22.3297, "lng": 87.3195, "platforms": 12},
    {"code": "MLDT", "name": "Malda Town", "city": "Malda", "district": "Malda", "state": "West Bengal", "zone": "ER", "lat": 25.0116, "lng": 88.1396, "platforms": 7},
    {"code": "NJP", "name": "New Jalpaiguri Junction", "city": "Siliguri", "district": "Jalpaiguri", "state": "West Bengal", "zone": "NFR", "lat": 26.6841, "lng": 88.4429, "platforms": 8},

    # Jharkhand (East Central Railway / South Eastern Railway)
    {"code": "DHN", "name": "Dhanbad Junction", "city": "Dhanbad", "district": "Dhanbad", "state": "Jharkhand", "zone": "ECR", "lat": 23.7917, "lng": 86.4304, "platforms": 8},
    {"code": "RNC", "name": "Ranchi Junction", "city": "Ranchi", "district": "Ranchi", "state": "Jharkhand", "zone": "SER", "lat": 23.3441, "lng": 85.3341, "platforms": 6},
    {"code": "TATA", "name": "Tatanagar Junction", "city": "Jamshedpur", "district": "East Singhbhum", "state": "Jharkhand", "zone": "SER", "lat": 22.7667, "lng": 86.2000, "platforms": 5},
    {"code": "BKSC", "name": "Bokaro Steel City", "city": "Bokaro", "district": "Bokaro", "state": "Jharkhand", "zone": "SER", "lat": 23.6693, "lng": 86.1511, "platforms": 5},
    {"code": "PNME", "name": "Parasnath", "city": "Isri", "district": "Giridih", "state": "Jharkhand", "zone": "ECR", "lat": 23.9781, "lng": 86.0469, "platforms": 4},
    {"code": "KQR", "name": "Koderma Junction", "city": "Jhumri Telaiya", "district": "Koderma", "state": "Jharkhand", "zone": "ECR", "lat": 24.4678, "lng": 85.5939, "platforms": 7},

    # Bihar (East Central Railway)
    {"code": "GAYA", "name": "Gaya Junction", "city": "Gaya", "district": "Gaya", "state": "Bihar", "zone": "ECR", "lat": 24.8028, "lng": 84.9994, "platforms": 9},
    {"code": "PNBE", "name": "Patna Junction", "city": "Patna", "district": "Patna", "state": "Bihar", "zone": "ECR", "lat": 25.6022, "lng": 85.1376, "platforms": 10},
    {"code": "DNR", "name": "Danapur", "city": "Patna", "district": "Patna", "state": "Bihar", "zone": "ECR", "lat": 25.6318, "lng": 85.0447, "platforms": 5},
    {"code": "PPTA", "name": "Patliputra Junction", "city": "Patna", "district": "Patna", "state": "Bihar", "zone": "ECR", "lat": 25.6372, "lng": 85.0886, "platforms": 5},
    {"code": "MFP", "name": "Muzaffarpur Junction", "city": "Muzaffarpur", "district": "Muzaffarpur", "state": "Bihar", "zone": "ECR", "lat": 26.1209, "lng": 85.3889, "platforms": 8},
    {"code": "DBG", "name": "Darbhanga Junction", "city": "Darbhanga", "district": "Darbhanga", "state": "Bihar", "zone": "ECR", "lat": 26.1542, "lng": 85.8918, "platforms": 5},
    {"code": "BJU", "name": "Barauni Junction", "city": "Barauni", "district": "Begusarai", "state": "Bihar", "zone": "ECR", "lat": 25.4744, "lng": 85.9758, "platforms": 9},
    {"code": "BGP", "name": "Bhagalpur Junction", "city": "Bhagalpur", "district": "Bhagalpur", "state": "Bihar", "zone": "ER", "lat": 25.2425, "lng": 87.0169, "platforms": 6},
    {"code": "KIR", "name": "Katihar Junction", "city": "Katihar", "district": "Katihar", "state": "Bihar", "zone": "NFR", "lat": 25.5392, "lng": 87.5714, "platforms": 9},
    {"code": "ARA", "name": "Ara Junction", "city": "Ara", "district": "Bhojpur", "state": "Bihar", "zone": "ECR", "lat": 25.5539, "lng": 84.6644, "platforms": 4},
    {"code": "BXR", "name": "Buxar", "city": "Buxar", "district": "Buxar", "state": "Bihar", "zone": "ECR", "lat": 25.5647, "lng": 83.9856, "platforms": 3},
    {"code": "DOS", "name": "Dehri On Sone", "city": "Dehri", "district": "Rohtas", "state": "Bihar", "zone": "ECR", "lat": 24.9125, "lng": 84.1856, "platforms": 6},
    {"code": "SSM", "name": "Sasaram Junction", "city": "Sasaram", "district": "Rohtas", "state": "Bihar", "zone": "ECR", "lat": 24.9536, "lng": 84.0322, "platforms": 7},

    # Uttar Pradesh (Northern Railway / North Eastern / North Central Railway)
    {"code": "DDU", "name": "Pt. Deen Dayal Upadhyaya Junction", "city": "Mughalsarai", "district": "Chandauli", "state": "Uttar Pradesh", "zone": "ECR", "lat": 25.2819, "lng": 83.1189, "platforms": 8},
    {"code": "BSB", "name": "Varanasi Junction (Cantonment)", "city": "Varanasi", "district": "Varanasi", "state": "Uttar Pradesh", "zone": "NR", "lat": 25.3267, "lng": 82.9864, "platforms": 9},
    {"code": "BSBS", "name": "Banaras (Manduadih)", "city": "Varanasi", "district": "Varanasi", "state": "Uttar Pradesh", "zone": "NER", "lat": 25.3117, "lng": 82.9647, "platforms": 8},
    {"code": "PRYJ", "name": "Prayagraj Junction (Allahabad)", "city": "Prayagraj", "district": "Prayagraj", "state": "Uttar Pradesh", "zone": "NCR", "lat": 25.4447, "lng": 81.8336, "platforms": 10},
    {"code": "CNB", "name": "Kanpur Central", "city": "Kanpur", "district": "Kanpur Nagar", "state": "Uttar Pradesh", "zone": "NCR", "lat": 26.4547, "lng": 80.3511, "platforms": 10},
    {"code": "LKO", "name": "Lucknow Charbagh", "city": "Lucknow", "district": "Lucknow", "state": "Uttar Pradesh", "zone": "NR", "lat": 26.8322, "lng": 80.9236, "platforms": 9},
    {"code": "LJN", "name": "Lucknow Junction (NER)", "city": "Lucknow", "district": "Lucknow", "state": "Uttar Pradesh", "zone": "NER", "lat": 26.8286, "lng": 80.9222, "platforms": 6},
    {"code": "GKP", "name": "Gorakhpur Junction", "city": "Gorakhpur", "district": "Gorakhpur", "state": "Uttar Pradesh", "zone": "NER", "lat": 26.7583, "lng": 83.3817, "platforms": 10},
    {"code": "AGC", "name": "Agra Cantt", "city": "Agra", "district": "Agra", "state": "Uttar Pradesh", "zone": "NCR", "lat": 27.1578, "lng": 77.9908, "platforms": 6},
    {"code": "AF", "name": "Agra Fort", "city": "Agra", "district": "Agra", "state": "Uttar Pradesh", "zone": "NCR", "lat": 27.1825, "lng": 78.0169, "platforms": 4},
    {"code": "MTJ", "name": "Mathura Junction", "city": "Mathura", "district": "Mathura", "state": "Uttar Pradesh", "zone": "NCR", "lat": 27.4925, "lng": 77.6736, "platforms": 10},
    {"code": "ALJN", "name": "Aligarh Junction", "city": "Aligarh", "district": "Aligarh", "state": "Uttar Pradesh", "zone": "NCR", "lat": 27.8964, "lng": 78.0772, "platforms": 7},
    {"code": "GZB", "name": "Ghaziabad Junction", "city": "Ghaziabad", "district": "Ghaziabad", "state": "Uttar Pradesh", "zone": "NR", "lat": 28.6672, "lng": 77.4339, "platforms": 6},
    {"code": "MB", "name": "Moradabad Junction", "city": "Moradabad", "district": "Moradabad", "state": "Uttar Pradesh", "zone": "NR", "lat": 28.8286, "lng": 78.7678, "platforms": 7},
    {"code": "BE", "name": "Bareilly Junction", "city": "Bareilly", "district": "Bareilly", "state": "Uttar Pradesh", "zone": "NR", "lat": 28.3375, "lng": 79.4189, "platforms": 6},
    {"code": "JHS", "name": "Virangana Lakshmibai Jhansi", "city": "Jhansi", "district": "Jhansi", "state": "Uttar Pradesh", "zone": "NCR", "lat": 25.4484, "lng": 78.5558, "platforms": 8},
    {"code": "AYC", "name": "Ayodhya Cantt", "city": "Ayodhya", "district": "Ayodhya", "state": "Uttar Pradesh", "zone": "NR", "lat": 26.7761, "lng": 82.1361, "platforms": 5},
    {"code": "AY", "name": "Ayodhya Dham Junction", "city": "Ayodhya", "district": "Ayodhya", "state": "Uttar Pradesh", "zone": "NR", "lat": 26.7936, "lng": 82.1994, "platforms": 6},

    # Delhi (Northern Railway)
    {"code": "NDLS", "name": "New Delhi", "city": "New Delhi", "district": "Central Delhi", "state": "Delhi", "zone": "NR", "lat": 28.6427, "lng": 77.2205, "platforms": 16},
    {"code": "DLI", "name": "Old Delhi Junction", "city": "Delhi", "district": "North Delhi", "state": "Delhi", "zone": "NR", "lat": 28.6606, "lng": 77.2281, "platforms": 16},
    {"code": "NZM", "name": "Hazrat Nizamuddin", "city": "New Delhi", "district": "South East Delhi", "state": "Delhi", "zone": "NR", "lat": 28.5889, "lng": 77.2536, "platforms": 7},
    {"code": "ANVT", "name": "Anand Vihar Terminal", "city": "Delhi", "district": "East Delhi", "state": "Delhi", "zone": "NR", "lat": 28.6508, "lng": 77.3153, "platforms": 7},
    {"code": "DEC", "name": "Delhi Cantt", "city": "New Delhi", "district": "South West Delhi", "state": "Delhi", "zone": "NR", "lat": 28.5911, "lng": 77.1264, "platforms": 4},
    {"code": "DEE", "name": "Delhi Sarai Rohilla", "city": "Delhi", "district": "Central Delhi", "state": "Delhi", "zone": "NR", "lat": 28.6653, "lng": 77.1883, "platforms": 7},

    # Maharashtra (Central Railway / Western Railway)
    {"code": "CSMT", "name": "Chhatrapati Shivaji Maharaj Terminus", "city": "Mumbai", "district": "Mumbai City", "state": "Maharashtra", "zone": "CR", "lat": 18.9400, "lng": 72.8353, "platforms": 18},
    {"code": "MMCT", "name": "Mumbai Central", "city": "Mumbai", "district": "Mumbai City", "state": "Maharashtra", "zone": "WR", "lat": 18.9694, "lng": 72.8194, "platforms": 9},
    {"code": "BDTS", "name": "Bandra Terminus", "city": "Mumbai", "district": "Mumbai Suburban", "state": "Maharashtra", "zone": "WR", "lat": 19.0600, "lng": 72.8422, "platforms": 7},
    {"code": "LTT", "name": "Lokmanya Tilak Terminus", "city": "Mumbai", "district": "Mumbai Suburban", "state": "Maharashtra", "zone": "CR", "lat": 19.0694, "lng": 72.8906, "platforms": 5},
    {"code": "KYN", "name": "Kalyan Junction", "city": "Kalyan", "district": "Thane", "state": "Maharashtra", "zone": "CR", "lat": 19.2372, "lng": 73.1306, "platforms": 8},
    {"code": "PUNE", "name": "Pune Junction", "city": "Pune", "district": "Pune", "state": "Maharashtra", "zone": "CR", "lat": 18.5289, "lng": 73.8744, "platforms": 6},
    {"code": "NGP", "name": "Nagpur Junction", "city": "Nagpur", "district": "Nagpur", "state": "Maharashtra", "zone": "CR", "lat": 21.1528, "lng": 79.0886, "platforms": 8},
    {"code": "BSL", "name": "Bhusaval Junction", "city": "Bhusawal", "district": "Jalgaon", "state": "Maharashtra", "zone": "CR", "lat": 21.0475, "lng": 75.7944, "platforms": 8},
    {"code": "NK", "name": "Nashik Road", "city": "Nashik", "district": "Nashik", "state": "Maharashtra", "zone": "CR", "lat": 19.9575, "lng": 73.8447, "platforms": 4},
    {"code": "SUR", "name": "Solapur", "city": "Solapur", "district": "Solapur", "state": "Maharashtra", "zone": "CR", "lat": 17.6599, "lng": 75.9064, "platforms": 5},
    {"code": "KOP", "name": "Chhatrapati Shahu Maharaj Terminus Kolhapur", "city": "Kolhapur", "district": "Kolhapur", "state": "Maharashtra", "zone": "CR", "lat": 16.7028, "lng": 74.2417, "platforms": 3},
    {"code": "AWB", "name": "Chhatrapati Sambhajinagar (Aurangabad)", "city": "Chhatrapati Sambhajinagar", "district": "Aurangabad", "state": "Maharashtra", "zone": "SCR", "lat": 19.8667, "lng": 75.3167, "platforms": 5},

    # Rajasthan (North Western Railway / West Central Railway)
    {"code": "JP", "name": "Jaipur Junction", "city": "Jaipur", "district": "Jaipur", "state": "Rajasthan", "zone": "NWR", "lat": 26.9197, "lng": 75.7878, "platforms": 8},
    {"code": "JU", "name": "Jodhpur Junction", "city": "Jodhpur", "district": "Jodhpur", "state": "Rajasthan", "zone": "NWR", "lat": 26.2847, "lng": 73.0186, "platforms": 5},
    {"code": "BKN", "name": "Bikaner Junction", "city": "Bikaner", "district": "Bikaner", "state": "Rajasthan", "zone": "NWR", "lat": 28.0167, "lng": 73.3119, "platforms": 6},
    {"code": "AII", "name": "Ajmer Junction", "city": "Ajmer", "district": "Ajmer", "state": "Rajasthan", "zone": "NWR", "lat": 26.4556, "lng": 74.6361, "platforms": 5},
    {"code": "UDZ", "name": "Udaipur City", "city": "Udaipur", "district": "Udaipur", "state": "Rajasthan", "zone": "NWR", "lat": 24.5714, "lng": 73.6989, "platforms": 5},
    {"code": "KOTA", "name": "Kota Junction", "city": "Kota", "district": "Kota", "state": "Rajasthan", "zone": "WCR", "lat": 25.2197, "lng": 75.8647, "platforms": 6},
    {"code": "BTE", "name": "Bharatpur Junction", "city": "Bharatpur", "district": "Bharatpur", "state": "Rajasthan", "zone": "WCR", "lat": 27.2389, "lng": 77.4989, "platforms": 3},
    {"code": "ABR", "name": "Abu Road", "city": "Abu Road", "district": "Sirohi", "state": "Rajasthan", "zone": "NWR", "lat": 24.4792, "lng": 72.7789, "platforms": 3},

    # Gujarat (Western Railway)
    {"code": "ADI", "name": "Ahmedabad Junction", "city": "Ahmedabad", "district": "Ahmedabad", "state": "Gujarat", "zone": "WR", "lat": 23.0231, "lng": 72.6006, "platforms": 12},
    {"code": "ST", "name": "Surat", "city": "Surat", "district": "Surat", "state": "Gujarat", "zone": "WR", "lat": 21.2047, "lng": 72.8408, "platforms": 4},
    {"code": "BRC", "name": "Vadodara Junction", "city": "Vadodara", "district": "Vadodara", "state": "Gujarat", "zone": "WR", "lat": 22.3106, "lng": 73.1811, "platforms": 7},
    {"code": "RJT", "name": "Rajkot Junction", "city": "Rajkot", "district": "Rajkot", "state": "Gujarat", "zone": "WR", "lat": 22.3117, "lng": 70.7972, "platforms": 5},
    {"code": "BH", "name": "Bharuch Junction", "city": "Bharuch", "district": "Bharuch", "state": "Gujarat", "zone": "WR", "lat": 21.7053, "lng": 72.9739, "platforms": 6},
    {"code": "GIMB", "name": "Gandhidham Junction", "city": "Gandhidham", "district": "Kutch", "state": "Gujarat", "zone": "WR", "lat": 23.0767, "lng": 70.1342, "platforms": 3},
    {"code": "BVC", "name": "Bhavnagar Terminus", "city": "Bhavnagar", "district": "Bhavnagar", "state": "Gujarat", "zone": "WR", "lat": 21.7644, "lng": 72.1389, "platforms": 3},

    # Tamil Nadu (Southern Railway)
    {"code": "MAS", "name": "Puratchi Thalaivar Dr. MGR Central", "city": "Chennai", "district": "Chennai", "state": "Tamil Nadu", "zone": "SR", "lat": 13.0825, "lng": 80.2750, "platforms": 17},
    {"code": "MS", "name": "Chennai Egmore", "city": "Chennai", "district": "Chennai", "state": "Tamil Nadu", "zone": "SR", "lat": 13.0789, "lng": 80.2608, "platforms": 11},
    {"code": "CBE", "name": "Coimbatore Junction", "city": "Coimbatore", "district": "Coimbatore", "state": "Tamil Nadu", "zone": "SR", "lat": 11.0017, "lng": 76.9658, "platforms": 6},
    {"code": "MDU", "name": "Madurai Junction", "city": "Madurai", "district": "Madurai", "state": "Tamil Nadu", "zone": "SR", "lat": 9.9172, "lng": 78.1103, "platforms": 8},
    {"code": "TPJ", "name": "Tiruchchirappalli Junction", "city": "Tiruchirappalli", "district": "Tiruchirappalli", "state": "Tamil Nadu", "zone": "SR", "lat": 10.7917, "lng": 78.6858, "platforms": 8},
    {"code": "SA", "name": "Salem Junction", "city": "Salem", "district": "Salem", "state": "Tamil Nadu", "zone": "SR", "lat": 11.6667, "lng": 78.1167, "platforms": 6},
    {"code": "TEN", "name": "Tirunelveli Junction", "city": "Tirunelveli", "district": "Tirunelveli", "state": "Tamil Nadu", "zone": "SR", "lat": 8.7289, "lng": 77.7125, "platforms": 5},
    {"code": "CAPE", "name": "Kanniyakumari", "city": "Kanyakumari", "district": "Kanyakumari", "state": "Tamil Nadu", "zone": "SR", "lat": 8.0883, "lng": 77.5386, "platforms": 4},

    # Karnataka (South Western Railway)
    {"code": "SBC", "name": "KSR Bengaluru City Junction", "city": "Bengaluru", "district": "Bengaluru Urban", "state": "Karnataka", "zone": "SWR", "lat": 12.9781, "lng": 77.5694, "platforms": 10},
    {"code": "YPR", "name": "Yesvantpur Junction", "city": "Bengaluru", "district": "Bengaluru Urban", "state": "Karnataka", "zone": "SWR", "lat": 13.0236, "lng": 77.5500, "platforms": 6},
    {"code": "SMVB", "name": "Sir M. Visvesvaraya Terminal", "city": "Bengaluru", "district": "Bengaluru Urban", "state": "Karnataka", "zone": "SWR", "lat": 13.0033, "lng": 77.6533, "platforms": 7},
    {"code": "MYS", "name": "Mysuru Junction", "city": "Mysuru", "district": "Mysuru", "state": "Karnataka", "zone": "SWR", "lat": 12.3167, "lng": 76.6500, "platforms": 6},
    {"code": "UBL", "name": "SSS Hubballi Junction", "city": "Hubballi", "district": "Dharwad", "state": "Karnataka", "zone": "SWR", "lat": 15.3458, "lng": 75.1481, "platforms": 8},
    {"code": "MAQ", "name": "Mangaluru Central", "city": "Mangaluru", "district": "Dakshina Kannada", "state": "Karnataka", "zone": "SR", "lat": 12.8639, "lng": 74.8425, "platforms": 3},
    {"code": "MAJN", "name": "Mangaluru Junction", "city": "Mangaluru", "district": "Dakshina Kannada", "state": "Karnataka", "zone": "SR", "lat": 12.8711, "lng": 74.8767, "platforms": 3},

    # Telangana (South Central Railway)
    {"code": "SC", "name": "Secunderabad Junction", "city": "Hyderabad", "district": "Hyderabad", "state": "Telangana", "zone": "SCR", "lat": 17.4339, "lng": 78.5036, "platforms": 10},
    {"code": "HYB", "name": "Hyderabad Deccan (Nampally)", "city": "Hyderabad", "district": "Hyderabad", "state": "Telangana", "zone": "SCR", "lat": 17.3917, "lng": 78.4686, "platforms": 6},
    {"code": "KCG", "name": "Kacheguda", "city": "Hyderabad", "district": "Hyderabad", "state": "Telangana", "zone": "SCR", "lat": 17.3878, "lng": 78.4975, "platforms": 5},
    {"code": "KZJ", "name": "Kazipet Junction", "city": "Warangal", "district": "Hanamkonda", "state": "Telangana", "zone": "SCR", "lat": 17.9781, "lng": 79.5256, "platforms": 4},
    {"code": "WL", "name": "Warangal", "city": "Warangal", "district": "Warangal", "state": "Telangana", "zone": "SCR", "lat": 17.9625, "lng": 79.6053, "platforms": 3},

    # Andhra Pradesh (South Central / East Coast Railway)
    {"code": "BZA", "name": "Vijayawada Junction", "city": "Vijayawada", "district": "NTR", "state": "Andhra Pradesh", "zone": "SCR", "lat": 16.5186, "lng": 80.6197, "platforms": 10},
    {"code": "VSKP", "name": "Visakhapatnam Junction", "city": "Visakhapatnam", "district": "Visakhapatnam", "state": "Andhra Pradesh", "zone": "ECoR", "lat": 17.7214, "lng": 83.2872, "platforms": 8},
    {"code": "TPTY", "name": "Tirupati", "city": "Tirupati", "district": "Tirupati", "state": "Andhra Pradesh", "zone": "SCR", "lat": 13.6289, "lng": 79.4194, "platforms": 5},
    {"code": "GNT", "name": "Guntur Junction", "city": "Guntur", "district": "Guntur", "state": "Andhra Pradesh", "zone": "SCR", "lat": 16.2975, "lng": 80.4439, "platforms": 7},
    {"code": "RJY", "name": "Rajahmundry", "city": "Rajahmundry", "district": "East Godavari", "state": "Andhra Pradesh", "zone": "SCR", "lat": 16.9939, "lng": 81.7761, "platforms": 3},

    # Kerala (Southern Railway)
    {"code": "TVC", "name": "Thiruvananthapuram Central", "city": "Thiruvananthapuram", "district": "Thiruvananthapuram", "state": "Kerala", "zone": "SR", "lat": 8.4869, "lng": 76.9531, "platforms": 5},
    {"code": "ERS", "name": "Ernakulam Junction (South)", "city": "Kochi", "district": "Ernakulam", "state": "Kerala", "zone": "SR", "lat": 9.9678, "lng": 76.2894, "platforms": 6},
    {"code": "ERN", "name": "Ernakulam Town (North)", "city": "Kochi", "district": "Ernakulam", "state": "Kerala", "zone": "SR", "lat": 9.9928, "lng": 76.2872, "platforms": 2},
    {"code": "CLT", "name": "Kozhikode Main", "city": "Kozhikode", "district": "Kozhikode", "state": "Kerala", "zone": "SR", "lat": 11.2464, "lng": 75.7825, "platforms": 4},
    {"code": "TCR", "name": "Thrissur", "city": "Thrissur", "district": "Thrissur", "state": "Kerala", "zone": "SR", "lat": 10.5161, "lng": 76.2089, "platforms": 4},

    # Madhya Pradesh (West Central Railway / North Central Railway)
    {"code": "BPL", "name": "Bhopal Junction", "city": "Bhopal", "district": "Bhopal", "state": "Madhya Pradesh", "zone": "WCR", "lat": 23.2678, "lng": 77.4114, "platforms": 6},
    {"code": "RKMP", "name": "Rani Kamlapati (Habibganj)", "city": "Bhopal", "district": "Bhopal", "state": "Madhya Pradesh", "zone": "WCR", "lat": 23.2081, "lng": 77.4372, "platforms": 5},
    {"code": "INDB", "name": "Indore Junction", "city": "Indore", "district": "Indore", "state": "Madhya Pradesh", "zone": "WR", "lat": 22.7172, "lng": 75.8681, "platforms": 6},
    {"code": "GWL", "name": "Gwalior Junction", "city": "Gwalior", "district": "Gwalior", "state": "Madhya Pradesh", "zone": "NCR", "lat": 26.2167, "lng": 78.1833, "platforms": 4},
    {"code": "JBP", "name": "Jabalpur", "city": "Jabalpur", "district": "Jabalpur", "state": "Madhya Pradesh", "zone": "WCR", "lat": 23.1667, "lng": 79.9500, "platforms": 6},
    {"code": "ET", "name": "Itarsi Junction", "city": "Itarsi", "district": "Narmadapuram", "state": "Madhya Pradesh", "zone": "WCR", "lat": 22.6136, "lng": 77.7561, "platforms": 7},
    {"code": "UJN", "name": "Ujjain Junction", "city": "Ujjain", "district": "Ujjain", "state": "Madhya Pradesh", "zone": "WR", "lat": 23.1817, "lng": 75.7761, "platforms": 8},

    # Odisha (East Coast Railway)
    {"code": "BBS", "name": "Bhubaneswar", "city": "Bhubaneswar", "district": "Khurda", "state": "Odisha", "zone": "ECoR", "lat": 20.2725, "lng": 85.8428, "platforms": 6},
    {"code": "PURI", "name": "Puri", "city": "Puri", "district": "Puri", "state": "Odisha", "zone": "ECoR", "lat": 19.8136, "lng": 85.8317, "platforms": 8},
    {"code": "CTC", "name": "Cuttack Junction", "city": "Cuttack", "district": "Cuttack", "state": "Odisha", "zone": "ECoR", "lat": 20.4625, "lng": 85.8944, "platforms": 5},
    {"code": "ROU", "name": "Rourkela Junction", "city": "Rourkela", "district": "Sundargarh", "state": "Odisha", "zone": "SER", "lat": 22.2253, "lng": 84.8872, "platforms": 5},

    # Punjab & Haryana & Chandigarh (Northern Railway)
    {"code": "ASR", "name": "Amritsar Junction", "city": "Amritsar", "district": "Amritsar", "state": "Punjab", "zone": "NR", "lat": 31.6339, "lng": 74.8656, "platforms": 8},
    {"code": "LDH", "name": "Ludhiana Junction", "city": "Ludhiana", "district": "Ludhiana", "state": "Punjab", "zone": "NR", "lat": 30.9083, "lng": 75.8569, "platforms": 7},
    {"code": "JUC", "name": "Jalandhar City", "city": "Jalandhar", "district": "Jalandhar", "state": "Punjab", "zone": "NR", "lat": 31.3264, "lng": 75.5786, "platforms": 5},
    {"code": "UMB", "name": "Ambala Cantt Junction", "city": "Ambala", "district": "Ambala", "state": "Haryana", "zone": "NR", "lat": 30.3347, "lng": 76.8336, "platforms": 8},
    {"code": "CDG", "name": "Chandigarh Junction", "city": "Chandigarh", "district": "Chandigarh", "state": "Chandigarh", "zone": "NR", "lat": 30.7042, "lng": 76.8286, "platforms": 6},

    # Assam & Northeast (Northeast Frontier Railway)
    {"code": "GHY", "name": "Guwahati", "city": "Guwahati", "district": "Kamrup Metropolitan", "state": "Assam", "zone": "NFR", "lat": 26.1831, "lng": 91.7517, "platforms": 7},
    {"code": "KYQ", "name": "Kamakhya Junction", "city": "Guwahati", "district": "Kamrup Metropolitan", "state": "Assam", "zone": "NFR", "lat": 26.1558, "lng": 91.7042, "platforms": 4},
    {"code": "DBRG", "name": "Dibrugarh", "city": "Dibrugarh", "district": "Dibrugarh", "state": "Assam", "zone": "NFR", "lat": 27.4725, "lng": 94.9119, "platforms": 5},

    # Jammu & Kashmir (Northern Railway)
    {"code": "JAT", "name": "Jammu Tawi", "city": "Jammu", "district": "Jammu", "state": "Jammu & Kashmir", "zone": "NR", "lat": 32.7061, "lng": 74.8803, "platforms": 3},
    {"code": "SVDK", "name": "Shri Mata Vaishno Devi Katra", "city": "Katra", "district": "Reasi", "state": "Jammu & Kashmir", "zone": "NR", "lat": 32.9939, "lng": 74.9317, "platforms": 5},

    # Uttarakhand (Northern Railway)
    {"code": "DDN", "name": "Dehradun", "city": "Dehradun", "district": "Dehradun", "state": "Uttarakhand", "zone": "NR", "lat": 30.3167, "lng": 78.0333, "platforms": 4},
    {"code": "HW", "name": "Haridwar", "city": "Haridwar", "district": "Haridwar", "state": "Uttarakhand", "zone": "NR", "lat": 29.9458, "lng": 78.1561, "platforms": 9},

    # Goa (Konkan Railway / South Western Railway)
    {"code": "MAO", "name": "Madgaon Junction", "city": "Margao", "district": "South Goa", "state": "Goa", "zone": "KR", "lat": 15.2750, "lng": 73.9781, "platforms": 4},
    {"code": "VSG", "name": "Vasco da Gama", "city": "Vasco da Gama", "district": "South Goa", "state": "Goa", "zone": "SWR", "lat": 15.3975, "lng": 73.8114, "platforms": 3},

    # Chhattisgarh (South East Central Railway)
    {"code": "R", "name": "Raipur Junction", "city": "Raipur", "district": "Raipur", "state": "Chhattisgarh", "zone": "SECR", "lat": 21.2583, "lng": 81.6317, "platforms": 7},
    {"code": "BSP", "name": "Bilaspur Junction", "city": "Bilaspur", "district": "Bilaspur", "state": "Chhattisgarh", "zone": "SECR", "lat": 22.0797, "lng": 82.1644, "platforms": 8},
]

def search_stations(query: str, state: Optional[str] = None, district: Optional[str] = None, limit: int = 15) -> List[Dict[str, Any]]:
    q = query.strip().lower()
    results = []
    
    for s in STATIONS_DB:
        if state and state != "ALL" and s["state"].lower() != state.lower():
            continue
        if district and district != "ALL" and s["district"].lower() != district.lower():
            continue
            
        if not q:
            results.append(s)
        else:
            code_match = s["code"].lower().startswith(q) or q in s["code"].lower()
            name_match = q in s["name"].lower()
            city_match = q in s["city"].lower()
            dist_match = q in s["district"].lower()
            state_match = q in s["state"].lower()
            
            if code_match or name_match or city_match or dist_match or state_match:
                score = 10 if s["code"].lower() == q else (5 if code_match else 1)
                results.append((score, s))
                
    if q:
        results.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in results[:limit]]
    return results[:limit]

def get_station_by_code(code: str) -> Optional[Dict[str, Any]]:
    c = code.strip().upper()
    for s in STATIONS_DB:
        if s["code"] == c:
            return s
    return None

def get_all_states() -> List[str]:
    return sorted(list(set(s["state"] for s in STATIONS_DB)))

def get_districts_by_state(state: str) -> List[str]:
    return sorted(list(set(s["district"] for s in STATIONS_DB if s["state"].lower() == state.lower())))

def get_stations_by_district(state: str, district: str) -> List[Dict[str, Any]]:
    return [s for s in STATIONS_DB if s["state"].lower() == state.lower() and s["district"].lower() == district.lower()]

def get_geographical_tree() -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
    tree: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    for s in STATIONS_DB:
        st = s["state"]
        dst = s["district"]
        tree.setdefault(st, {}).setdefault(dst, []).append({
            "code": s["code"],
            "name": s["name"],
            "city": s["city"],
            "platforms": s["platforms"],
            "zone": s["zone"],
            "lat": s["lat"],
            "lng": s["lng"]
        })
    return tree
