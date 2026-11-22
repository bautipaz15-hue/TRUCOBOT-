import torch
import torch.nn as nn
import torch.nn.functional as F

class TrucoActorCritic(nn.Module):
    """
    Red Neuronal Actor-Critic para el bot de Truco.
    Toma el estado del entorno y devuelve:
    1. Las probabilidades de las acciones (Policy / Actor).
    2. El Valor Esperado del estado (Value / Critic).
    """
    def __init__(self, state_dim, num_actions, hidden_size=128):
        super(TrucoActorCritic, self).__init__()
        
        # Base compartida (Feature Extractor) - Reducido a MLP pequeño y rápido para CPU
        self.fc1 = nn.Linear(state_dim, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        
        # Actor Head (Policy)
        self.actor_fc = nn.Linear(hidden_size, hidden_size)
        self.actor_out = nn.Linear(hidden_size, num_actions)
        
        # Critic Head (Value expected)
        self.critic_fc = nn.Linear(hidden_size, hidden_size)
        self.critic_out = nn.Linear(hidden_size, 1)
        
        self.dropout = nn.Dropout(p=0.1)

    def forward(self, state, action_mask=None):
        """
        Forward pass. Si se provee action_mask, se enmascaran las acciones ilegales.
        
        state: Tensor de shape (batch_size, state_dim)
        action_mask: Tensor booleano de shape (batch_size, num_actions)
        """
        # Feature extraction
        x = F.relu(self.fc1(state))
        x = self.dropout(x)
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        
        # Valor del estado (Critic)
        v = F.relu(self.critic_fc(x))
        value = self.critic_out(v)
        
        # Probabilidades de acción (Actor)
        a = F.relu(self.actor_fc(x))
        logits = self.actor_out(a)
        
        if action_mask is not None:
            # Action Masking: Pone -inf (o un valor muy bajo) a las acciones no permitidas
            # Así, al hacer Softmax, la probabilidad de esas acciones será exactamente 0.
            # torch.where(condition, if_true, if_false)
            LARGE_NEGATIVE = -1e9
            logits = torch.where(action_mask, logits, torch.tensor(LARGE_NEGATIVE, dtype=logits.dtype, device=logits.device))
            
        # Devolvemos los logits brutos y el valor.
        # Las probabilidades finales se obtienen aplicando Softmax sobre los logits o usando torch.distributions.Categorical.
        return logits, value

    def get_action_and_value(self, state, action_mask, action=None):
        """
        Método utilitario para muestrear una acción de forma estocástica durante el entrenamiento
        o evaluar una acción específica (log_prob y entropía).
        """
        logits, value = self.forward(state, action_mask)
        
        probs = F.softmax(logits, dim=-1)
        dist = torch.distributions.Categorical(probs)
        
        if action is None:
            action = dist.sample()
            
        log_prob = dist.log_prob(action)
        entropy = dist.entropy()
        
        return action, log_prob, entropy, value
