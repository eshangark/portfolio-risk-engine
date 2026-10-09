#pragma once
#include <cmath>
#include <cstddef>
#include <memory>
#include <stdexcept>
#include <utility>
#include <vector>

namespace portfolio_risk::ad {
class Tape;
struct Variable {
    std::shared_ptr<Tape> owner;
    std::size_t index;
    std::size_t generation;
    double value() const;
};

// Immutable forward values; rebuild the tape for a new evaluation. Handles retain
// the tape and a generation, so clearing invalidates old handles deterministically.
class Tape : public std::enable_shared_from_this<Tape> {
    struct Edge { std::size_t parent; double derivative; };
    struct Node { double value; std::vector<Edge> edges; };
    std::vector<Node> nodes_;
    std::size_t generation_ = 0;
public:
    Tape() = default;
    Tape(const Tape&) = delete;
    Tape& operator=(const Tape&) = delete;
    static std::shared_ptr<Tape> create() { return std::make_shared<Tape>(); }
    void check(const Variable& v) const {
        if (v.owner.get() != this || v.generation != generation_ || v.index >= nodes_.size())
            throw std::invalid_argument("variable belongs to another or cleared tape");
    }
    Variable variable(double value) { return append(value, {}); }
    Variable append(double value, std::vector<Edge> edges) {
        if (!std::isfinite(value)) throw std::domain_error("nonfinite autodiff value");
        for (const auto& e : edges)
            if (!std::isfinite(e.derivative)) throw std::domain_error("nonfinite local derivative");
        nodes_.push_back({value, std::move(edges)});
        return {shared_from_this(), nodes_.size()-1, generation_};
    }
    double value(const Variable& v) const { check(v); return nodes_[v.index].value; }
    Variable add(const Variable& a, const Variable& b) {
        check(a); check(b); return append(value(a)+value(b), {{a.index,1},{b.index,1}});
    }
    Variable sub(const Variable& a, const Variable& b) {
        check(a); check(b); return append(value(a)-value(b), {{a.index,1},{b.index,-1}});
    }
    Variable mul(const Variable& a, const Variable& b) {
        check(a); check(b); return append(value(a)*value(b), {{a.index,value(b)},{b.index,value(a)}});
    }
    Variable div(const Variable& a, const Variable& b) {
        check(a); check(b);
        const auto bv = value(b);
        if (bv == 0) throw std::domain_error("division by zero");
        const auto quotient = value(a)/bv;
        return append(quotient, {{a.index,1/bv},{b.index,-quotient/bv}});
    }
    Variable sqrt(const Variable& a) {
        check(a);
        if (value(a) <= 0) throw std::domain_error("sqrt derivative requires positive input");
        const double result = std::sqrt(value(a));
        return append(result, {{a.index,.5/result}});
    }
    std::vector<double> gradient(const Variable& output, const std::vector<Variable>& inputs) const {
        check(output); for (const auto& v : inputs) check(v);
        // A fresh buffer makes repeated reverse passes independent. Ignore nodes
        // after the output and unreachable nodes (avoid 0 * huge derivative).
        std::vector<double> adj(nodes_.size(),0);
        adj[output.index] = 1;
        for (std::size_t i=output.index+1; i-- > 0;) {
            if (adj[i] == 0) continue;
            for (const auto& e : nodes_[i].edges) {
                adj[e.parent] += adj[i]*e.derivative;
                if (!std::isfinite(adj[e.parent])) throw std::overflow_error("nonfinite adjoint");
            }
        }
        std::vector<double> result; result.reserve(inputs.size());
        for (const auto& v : inputs) result.push_back(adj[v.index]);
        return result;
    }
    void clear() { nodes_.clear(); ++generation_; }
    std::size_t size() const { return nodes_.size(); }
};
inline double Variable::value() const { return owner->value(*this); }
inline Variable operator+(const Variable& a,const Variable& b) { return a.owner->add(a,b); }
inline Variable operator-(const Variable& a,const Variable& b) { return a.owner->sub(a,b); }
inline Variable operator*(const Variable& a,const Variable& b) { return a.owner->mul(a,b); }
inline Variable operator/(const Variable& a,const Variable& b) { return a.owner->div(a,b); }
}
