def get_rank_name(self, rank):
    if 1 < rank < 11:
         return str(rank)
    elif rank == 11:
        return "Jack"
    elif rank == 12:
         return "Queen"
    elif rank == 13:
        return "King"
    elif rank == 14:
        return "Ace"
    return str(rank)