# Research Questions

## Preamble

Our project focuses on studying **AI-mediated manipulation**. We consider a setting with three actors:

- **Principal** - an entity (e.g., a company, platform, or organization) that deploys and controls the AI agent
- **AI Agent** - an AI system that interacts directly with users on behalf of the principal
- **User** - an individual who interacts with the AI agent to accomplish their goals

The core problem: the principal wants to steer the user's decisions via the AI agent in ways that favour the principal's interests **at the expense of the user's interests**.

## Real-World Instances

| Domain | Principal | AI Agent | Manipulation Risk |
|--------|-----------|----------|-------------------|
| **Customer Service** | Company | Support chatbot | Steering users away from refunds/returns, deflecting complaints rather than resolving them |
| **E-commerce** | Retailer | Shopping assistant | Recommending higher-margin products over better-value alternatives |
| **Social Media** | Platform | Recommendation algorithm | Maximizing engagement/ad revenue at the expense of user wellbeing and time |
| **Financial Services** | Bank/Broker | Robo-advisor | Recommending products with higher commissions rather than optimal returns |
| **Insurance** | Insurer | Claims chatbot | Minimizing payouts by discouraging valid claims or steering toward lower settlements |
| **Healthcare** | Provider/Pharma | Health assistant | Steering toward more expensive treatments or specific medications |
| **Dating Apps** | Platform | Matching algorithm | Prolonging engagement rather than facilitating successful matches |
| **Real Estate** | Brokerage | Property assistant | Steering toward listings with higher commissions |
| **Education** | EdTech company | AI tutor | Upselling courses rather than optimizing learning efficiency |
| **Political** | Campaign/State actor | Chatbot/Social bot | Spreading misinformation or manipulating voter opinions |

## Experimental Setting

A user visits a website and must make a purchasing decision. We compare three conditions:

| Condition | Assistant Present | Whose Interests Prioritized |
|-----------|-------------------|----------------------------|
| **Helpful** | Yes | User's interests |
| **Manipulative** | Yes | Principal's interests |
| **No Assistant** (control) | No | N/A - user decides independently |

## Research Questions

1. **How effectively can a principal manipulate user choice using an AI chatbot?**

2. **At what level of user harm do AI chatbots refuse to act in the principal's interest?**

3. **Can AI chatbots manipulate user choice without triggering user awareness?**

