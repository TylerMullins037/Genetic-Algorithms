import random
import numpy as np
from scipy.special import softmax
# Constants
ROOMS = {
    "Slater 003": 45,
    "Roman 216": 30,
    "Loft 206": 75,
    "Roman 201": 50,
    "Loft 310": 108,
    "Beach 201": 60,
    "Beach 301": 75,
    "Logos 325": 450,
    "Frank 119": 60
}
TIME_SLOTS = ["10 AM", "11 AM", "12 PM", "1 PM", "2 PM", "3 PM"]
FACILITATORS = ["Lock", "Glen", "Banks", "Richards", "Shaw", "Singer", "Uther", "Tyler", "Numen", "Zeldin"]

class Activity:
    def __init__(self, name, expected_enrollment, preferred, other):
        self.name = name
        self.expected_enrollment = expected_enrollment
        self.preferred_facilitators = preferred
        self.other_facilitators = other
        self.room = None
        self.time_slot = None
        self.facilitator = None


# Initialize activities
activities = [
    Activity("SLA101A", 50, ["Glen", "Lock", "Banks", "Zeldin"], ["Numen", "Richards"]),
    Activity("SLA101B", 50, ["Glen", "Lock", "Banks", "Zeldin"], ["Numen", "Richards"]),

    Activity("SLA191A", 50, ["Glen", "Lock", "Banks", "Zeldin"], ["Numen", "Richards"]),
    Activity("SLA191B", 50, ["Glen", "Lock", "Banks", "Zeldin"], ["Numen", "Richards"]),
   
    Activity("SLA201", 50, ["Glen", "Banks", "Zeldin", "Shaw"], ["Numen", "Richards", "Singer"]),
    Activity("SLA291", 50, ["Lock", "Banks", "Zeldin", "Singer"], ["Numen", "Richards", "Shaw", "Tyler"]),

    Activity("SLA303", 60, ["Glen", "Zeldin", "Banks"], ["Numen", "Singer", "Shaw"]),
    Activity("SLA304", 25, ["Glen", "Banks", "Tyler"], ["Numen", "Singer", "Shaw", "Richards", "Uther", "Zeldin"]),

    Activity("SLA394", 20, ["Tyler", "Singer"], ["Richards", "Zeldin"]),
    Activity("SLA449", 50, ["Tyler", "Singer", "Shaw"], ["Zeldin", "Uther"]),

    Activity("SLA451", 100, ["Tyler", "Singer", "Shaw"], ["Zeldin", "Uther", "Richards", "Banks"]),
    
]

# Schedule class
class Schedule:
    def __init__(self):
        self.assignments = []
        for activity in activities:
            assignment = {
                "activity": activity,
                "room": random.choice(list(ROOMS.keys())),
                "time_slot": random.choice(TIME_SLOTS),
                "facilitator": random.choice(FACILITATORS)
            }
            self.assignments.append(assignment)

    def fitness(self):
        score = 0
        time_slot_activity_map = {}
        facilitator_load = {f: 0 for f in FACILITATORS}
        # Store SLA 101 and SLA 191 sections for specific adjustments
        sla101_sections = []
        sla191_sections = []

        for assignment in self.assignments:
            activity = assignment["activity"]
            room = assignment["room"]
            time_slot = assignment["time_slot"]
            facilitator = assignment["facilitator"]

            # Fitness starts at 0 for each activity
            activity_fitness = 0 # check

            # Check for time slot collisions
            if time_slot not in time_slot_activity_map:
                time_slot_activity_map[time_slot] = []
            time_slot_activity_map[time_slot].append(assignment)

            # Room size checks
            room_capacity = ROOMS[room]
            if room_capacity < activity.expected_enrollment:  
                activity_fitness -= 0.5  # Room too small
            elif room_capacity > 6 * activity.expected_enrollment: 
                activity_fitness -= 0.4  # Room too big
            elif room_capacity > 3 * activity.expected_enrollment:  
                activity_fitness -= 0.2  # Slightly too big
            else:  
                activity_fitness += 0.3  # Just right

            # Facilitator preferences
            if facilitator in activity.preferred_facilitators:  
                activity_fitness += 0.5  # Preferred facilitator
            elif facilitator in activity.other_facilitators:  
                activity_fitness += 0.2  # Other facilitator
            else:  
                activity_fitness -= 0.1  # Some other facilitator

            # Track facilitator load
            facilitator_load[facilitator] += 1
            
            # Store sections for SLA101 and SLA191 for specific adjustments
            if activity.name.startswith("SLA101"):
                sla101_sections.append(assignment)
            elif activity.name.startswith("SLA191"):
                sla191_sections.append(assignment)

            # Add activity fitness to total score
            score += activity_fitness

        facilitator_time_slots = {}
        for time_slot, assignments in time_slot_activity_map.items():
            room_activity_map = {}
            # Group activities by room within each time slot
            for assignment in assignments:
                room = assignment["room"]
                facilitator = assignment["facilitator"]

                if facilitator not in facilitator_time_slots:
                    facilitator_time_slots[facilitator] = []
                facilitator_time_slots[facilitator].append(time_slot)

                if room not in room_activity_map:
                    room_activity_map[room] = []
                room_activity_map[room].append(assignment)
        
            # Check if multiple activities are in the same room at the same time slot
            for room, activities_in_room in room_activity_map.items():
                if len(activities_in_room) > 1:  
                    score -= 0.5  # Apply penalty for room conflict at the same time slot

            facilitators_in_slot = [a["facilitator"] for a in assignments]
            unique_facilitators = set(facilitators_in_slot)

            # Apply penalties for facilitators scheduled for the same time slot
            for facilitator in unique_facilitators:
                
                if facilitators_in_slot.count(facilitator) > 1: 
                    score -= 0.2  # More than one activity at the same time
                elif facilitators_in_slot.count(facilitator) == 1:  
                    score += 0.2  # Only one activity in this time slot

        # Facilitator load penalties
        for facilitator, load in facilitator_load.items():
            if load > 4:
                score -= 0.5  # Too many activities
            elif load == 1 or load ==2:  
                if facilitator != "Tyler":
                    score -= 0.4

        # Activity-specific adjustments for SLA 101
        if len(sla101_sections) == 2:  # check
            if sla101_sections[0]["time_slot"] == sla101_sections[1]["time_slot"]:
                score -= 0.5  # Same time slot penalty
            elif abs(TIME_SLOTS.index(sla101_sections[0]["time_slot"]) - TIME_SLOTS.index(sla101_sections[1]["time_slot"])) > 4:
                score += 0.5  # More than 4 hours apart bonus

        # Activity-specific adjustments for SLA 191
        if len(sla191_sections) == 2:  # check
            if sla191_sections[0]["time_slot"] == sla191_sections[1]["time_slot"]:
                score -= 0.5  # Same time slot penalty
            elif abs(TIME_SLOTS.index(sla191_sections[0]["time_slot"]) - TIME_SLOTS.index(sla191_sections[1]["time_slot"])) > 4:
                score += 0.5  # More than 4 hours apart bonus

        # Check for consecutive time slots between SLA 101 and SLA 191
        if sla101_sections and sla191_sections:  # check
            for sla101 in sla101_sections:
                for sla191 in sla191_sections:
                    if abs(TIME_SLOTS.index(sla101["time_slot"]) - TIME_SLOTS.index(sla191["time_slot"])) == 1:
                        score += 0.5  # (0.5) Consecutive time slots
                        # Penalize if one is in specific rooms
                        if ((sla101["room"] in ["Roman 216","Roman 201", "Beach 201", "Beach 301"] and 
                            sla191["room"] not in ["Roman 216","Roman 201", "Beach 201", "Beach 301"]) or 
                            (sla191 in ["Roman 216","Roman 201", "Beach 201", "Beach 301"] and 
                             sla101 not in ["Roman 216","Roman 201", "Beach 201", "Beach 301"])):
                            score -= 0.4


                    elif abs(TIME_SLOTS.index(sla101["time_slot"]) - TIME_SLOTS.index(sla191["time_slot"])) == 2:
                        score += 0.25  # One-hour separation bonus

                    elif sla101["time_slot"] == sla191["time_slot"]:
                        score -= 0.25  # Same time slot penalty

        for facilitator, time_slots in facilitator_time_slots.items():
            time_slots = sorted([TIME_SLOTS.index(ts) for ts in time_slots])
            for i in range(len(time_slots) - 1):  # check 
                if time_slots[i + 1] - time_slots[i] == 1:
                    score += 0.5  # Consecutive time slots
                    activities_in_consecutive_slots = [
                    assignment for assignment in self.assignments 
                    if assignment["facilitator"] == facilitator and 
                    TIME_SLOTS.index(assignment["time_slot"]) in [time_slots[i], time_slots[i + 1]]
                ]
                    if len(activities_in_consecutive_slots) == 2:
                        room_1, room_2 = activities_in_consecutive_slots[0]["room"], activities_in_consecutive_slots[1]["room"]
                        if ((room_1 in ["Roman 216","Roman 201", "Beach 201", "Beach 301"] and 
                            room_2 not in ["Roman 216","Roman 201", "Beach 201", "Beach 301"]) or
                            (room_2 in ["Roman 216","Roman 201", "Beach 201", "Beach 301"] and 
                            room_1 not in ["Roman 216","Roman 201", "Beach 201", "Beach 301"])):
                            score -= 0.4  # Widely separated penalty      
        return score
    
def genetic_algorithm(population_size=10000, generations=1000, mutation_rate=0.01):
    # Initialize population
    population = [Schedule() for _ in range(population_size)]
    previous_avg = 0

    for generation in range(generations):
        # Evaluate fitness and sort by score
        fitness_scores = np.array([s.fitness() for s in population])
        probabilities = softmax(fitness_scores)
       
        # Stop if the best fitness is stable
        if generation > 100:  # Check earlier
            avg = np.mean(fitness_scores)
            if abs(avg - previous_avg) < 0.01 * previous_avg:
                print("Early stopping at Generation: " + str(generation))
                break
            previous_avg = avg

        selected_indices = np.random.choice(np.arange(population_size), size=population_size, p=probabilities)
        selected_population = [population[i] for i in selected_indices]

        # Create next generation
        next_generation = []
        while len(next_generation) < population_size:
            parent1, parent2 = random.sample(selected_population[:population_size // 2], 2)
            # Crossover
            child1 = Schedule()
            child2 = Schedule()
            for i in range(len(activities)):
                if random.random() < 0.5:
                    child1.assignments[i] = parent1.assignments[i].copy()  # Ensure deep copy
                else:
                    child1.assignments[i] = parent2.assignments[i].copy()
                
                if random.random() < 0.5:
                    child2.assignments[i] = parent1.assignments[i].copy()
                else:
                    child2.assignments[i] = parent2.assignments[i].copy()

            # Mutation
            for child in [child1, child2]:
                for assignment in child.assignments:
                    if random.random() < mutation_rate:  # Mutate based on mutation rate
                        mutation_choice = random.choice(["room", "time_slot", "facilitator"])
                        if mutation_choice == "room":
                            assignment["room"] = random.choice(list(ROOMS.keys()))
                        elif mutation_choice == "time_slot":
                            assignment["time_slot"] = random.choice(TIME_SLOTS)
                        elif mutation_choice == "facilitator":
                            assignment["facilitator"] = random.choice(FACILITATORS)

            next_generation.extend([child1, child2])

        population = next_generation[:population_size]

    # Return the best schedule from the last generation
    best_schedule = population[0]
    return best_schedule


best_schedule = genetic_algorithm()
print("Best schedule fitness:", round(best_schedule.fitness(),2))

print("\nBest Schedule:")
for assignment in best_schedule.assignments:
    activity = assignment["activity"].name
    room = assignment["room"]
    time_slot = assignment["time_slot"]
    facilitator = assignment["facilitator"]
    print(f"Activity: {activity}, Room: {room}, Time: {time_slot}, Facilitator: {facilitator}")

