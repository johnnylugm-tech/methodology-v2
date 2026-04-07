"""Marketplace for methodology-v2"""
import uuid, time
from typing import List, Dict, Optional
from dataclasses import dataclass, field

@dataclass
class Template:
    template_id: str = field(default_factory=lambda: f"tpl_{uuid.uuid4().hex[:8]}")
    name: str = ""
    description: str = ""
    category: str = "custom"
    price: float = 0.0
    rating: float = 0.0
    reviews: int = 0
    code_url: str = ""
    author: str = ""
    created_at: float = field(default_factory=time.time)

@dataclass
class Review:
    review_id: str
    rating: int
    review: str
    author: str
    created_at: float

class Marketplace:
    templates: List[Template] = []
    reviews: Dict[str, List[Review]] = {}
    
    @classmethod
    def list_templates(cls, category: str = None) -> List[Template]:
        if category:
            return [t for t in cls.templates if t.category == category]
        return cls.templates
    
    @classmethod
    def search(cls, query: str) -> List[Template]:
        q = query.lower()
        return [t for t in cls.templates if q in t.name.lower() or q in t.description.lower()]
    
    @classmethod
    def filter(cls, category=None, min_rating=0.0, free_only=False) -> List[Template]:
        results = cls.templates
        if category: results = [t for t in results if t.category == category]
        if min_rating > 0: results = [t for t in results if t.rating >= min_rating]
        if free_only: results = [t for t in results if t.price == 0]
        return results
    
    @classmethod
    def install(cls, template_id: str) -> bool:
        for t in cls.templates:
            if t.template_id == template_id:
                print(f"Installed: {t.name}")
                return True
        return False
    
    @classmethod
    def publish(cls, template: Template):
        cls.templates.append(template)
        return template.template_id
    
    @classmethod
    def rate(cls, template_id: str, rating: int, review: str, author: str = "anonymous"):
        if template_id not in cls.reviews:
            cls.reviews[template_id] = []
        cls.reviews[template_id].append(Review(str(uuid.uuid4()), rating, review, author))
        # Update average
        for t in cls.templates:
            if t.template_id == template_id:
                r = cls.reviews[template_id]
                t.rating = sum(x.rating for x in r) / len(r)
                t.reviews = len(r)

if __name__ == "__main__":
    t1 = Template(name="Customer Bot", description="客服机器人", category="customer_service")
    Marketplace.publish(t1)
    print(f"Published: {t1.template_id}")
    print(Marketplace.list_templates())
