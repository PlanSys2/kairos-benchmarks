(define (problem drill-2) (:domain drill) (:objects h1 h2 - hole)
(:init (bit_free) (= (rate) 1.5) (planned h1) (= (depth h1) 0) (= (min_depth h1) 12) (= (max_depth h1) 15) (planned h2) (= (depth h2) 0) (= (min_depth h2) 17) (= (max_depth h2) 20))
(:goal (and (drilled h1) (drilled h2))))
