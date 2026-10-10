class KnowledgeBase:
    def __init__(self):
        self.facts = set()   # unique facts, e.g. "TargetVisible"
        self.rules = []      # (premise_list, conclusion) tuples

    def tell_fact(self, fact):
        self.facts.add(fact)

    def tell_rule(self, premises, conclusion):
        self.rules.append((premises, conclusion))

    def clear_facts(self):
        self.facts.clear()
    
    def forward_chain(self):
        new_facts_added = True

        # Keep looping until a full pass adds no new facts
        while new_facts_added:
            new_facts_added = False

            for premises, conclusion in self.rules:
                if conclusion not in self.facts:
                    # Modus Ponens: if all premises are true, the conclusion is true
                    if all(p in self.facts for p in premises):
                        self.facts.add(conclusion)
                        new_facts_added = True

