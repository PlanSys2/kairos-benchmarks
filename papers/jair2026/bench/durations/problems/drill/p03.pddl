(define (problem drill-3) (:domain drill) (:objects h1 h2 h3 - hole)
(:init (bit_free) (= (rate) 1.5) (planned h1) (= (depth h1) 0) (= (min_depth h1) 12) (= (max_depth h1) 15) (planned h2) (= (depth h2) 0) (= (min_depth h2) 17) (= (max_depth h2) 20) (planned h3) (= (depth h3) 0) (= (min_depth h3) 22) (= (max_depth h3) 25))
(:goal (and (drilled h1) (drilled h2) (drilled h3))))
