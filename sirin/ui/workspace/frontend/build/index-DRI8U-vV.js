var Do = { exports: {} }, Er = {}, Vo = { exports: {} }, Q = {};
/**
 * @license React
 * react.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var Ha;
function uf() {
  if (Ha) return Q;
  Ha = 1;
  var u = Symbol.for("react.element"), a = Symbol.for("react.portal"), c = Symbol.for("react.fragment"), y = Symbol.for("react.strict_mode"), x = Symbol.for("react.profiler"), E = Symbol.for("react.provider"), L = Symbol.for("react.context"), T = Symbol.for("react.forward_ref"), R = Symbol.for("react.suspense"), w = Symbol.for("react.memo"), B = Symbol.for("react.lazy"), A = Symbol.iterator;
  function Z(h) {
    return h === null || typeof h != "object" ? null : (h = A && h[A] || h["@@iterator"], typeof h == "function" ? h : null);
  }
  var oe = { isMounted: function() {
    return !1;
  }, enqueueForceUpdate: function() {
  }, enqueueReplaceState: function() {
  }, enqueueSetState: function() {
  } }, ce = Object.assign, K = {};
  function V(h, S, J) {
    this.props = h, this.context = S, this.refs = K, this.updater = J || oe;
  }
  V.prototype.isReactComponent = {}, V.prototype.setState = function(h, S) {
    if (typeof h != "object" && typeof h != "function" && h != null) throw Error("setState(...): takes an object of state variables to update or a function which returns an object of state variables.");
    this.updater.enqueueSetState(this, h, S, "setState");
  }, V.prototype.forceUpdate = function(h) {
    this.updater.enqueueForceUpdate(this, h, "forceUpdate");
  };
  function re() {
  }
  re.prototype = V.prototype;
  function Ee(h, S, J) {
    this.props = h, this.context = S, this.refs = K, this.updater = J || oe;
  }
  var Ne = Ee.prototype = new re();
  Ne.constructor = Ee, ce(Ne, V.prototype), Ne.isPureReactComponent = !0;
  var de = Array.isArray, X = Object.prototype.hasOwnProperty, fe = { current: null }, Se = { key: !0, ref: !0, __self: !0, __source: !0 };
  function ye(h, S, J) {
    var G, _ = {}, b = null, le = null;
    if (S != null) for (G in S.ref !== void 0 && (le = S.ref), S.key !== void 0 && (b = "" + S.key), S) X.call(S, G) && !Se.hasOwnProperty(G) && (_[G] = S[G]);
    var ne = arguments.length - 2;
    if (ne === 1) _.children = J;
    else if (1 < ne) {
      for (var pe = Array(ne), en = 0; en < ne; en++) pe[en] = arguments[en + 2];
      _.children = pe;
    }
    if (h && h.defaultProps) for (G in ne = h.defaultProps, ne) _[G] === void 0 && (_[G] = ne[G]);
    return { $$typeof: u, type: h, key: b, ref: le, props: _, _owner: fe.current };
  }
  function Ze(h, S) {
    return { $$typeof: u, type: h.type, key: S, ref: h.ref, props: h.props, _owner: h._owner };
  }
  function Ae(h) {
    return typeof h == "object" && h !== null && h.$$typeof === u;
  }
  function $e(h) {
    var S = { "=": "=0", ":": "=2" };
    return "$" + h.replace(/[=:]/g, function(J) {
      return S[J];
    });
  }
  var We = /\/+/g;
  function ee(h, S) {
    return typeof h == "object" && h !== null && h.key != null ? $e("" + h.key) : S.toString(36);
  }
  function ze(h, S, J, G, _) {
    var b = typeof h;
    (b === "undefined" || b === "boolean") && (h = null);
    var le = !1;
    if (h === null) le = !0;
    else switch (b) {
      case "string":
      case "number":
        le = !0;
        break;
      case "object":
        switch (h.$$typeof) {
          case u:
          case a:
            le = !0;
        }
    }
    if (le) return le = h, _ = _(le), h = G === "" ? "." + ee(le, 0) : G, de(_) ? (J = "", h != null && (J = h.replace(We, "$&/") + "/"), ze(_, S, J, "", function(en) {
      return en;
    })) : _ != null && (Ae(_) && (_ = Ze(_, J + (!_.key || le && le.key === _.key ? "" : ("" + _.key).replace(We, "$&/") + "/") + h)), S.push(_)), 1;
    if (le = 0, G = G === "" ? "." : G + ":", de(h)) for (var ne = 0; ne < h.length; ne++) {
      b = h[ne];
      var pe = G + ee(b, ne);
      le += ze(b, S, J, pe, _);
    }
    else if (pe = Z(h), typeof pe == "function") for (h = pe.call(h), ne = 0; !(b = h.next()).done; ) b = b.value, pe = G + ee(b, ne++), le += ze(b, S, J, pe, _);
    else if (b === "object") throw S = String(h), Error("Objects are not valid as a React child (found: " + (S === "[object Object]" ? "object with keys {" + Object.keys(h).join(", ") + "}" : S) + "). If you meant to render a collection of children, use an array instead.");
    return le;
  }
  function De(h, S, J) {
    if (h == null) return h;
    var G = [], _ = 0;
    return ze(h, G, "", "", function(b) {
      return S.call(J, b, _++);
    }), G;
  }
  function Oe(h) {
    if (h._status === -1) {
      var S = h._result;
      S = S(), S.then(function(J) {
        (h._status === 0 || h._status === -1) && (h._status = 1, h._result = J);
      }, function(J) {
        (h._status === 0 || h._status === -1) && (h._status = 2, h._result = J);
      }), h._status === -1 && (h._status = 0, h._result = S);
    }
    if (h._status === 1) return h._result.default;
    throw h._result;
  }
  var se = { current: null }, k = { transition: null }, F = { ReactCurrentDispatcher: se, ReactCurrentBatchConfig: k, ReactCurrentOwner: fe };
  function P() {
    throw Error("act(...) is not supported in production builds of React.");
  }
  return Q.Children = { map: De, forEach: function(h, S, J) {
    De(h, function() {
      S.apply(this, arguments);
    }, J);
  }, count: function(h) {
    var S = 0;
    return De(h, function() {
      S++;
    }), S;
  }, toArray: function(h) {
    return De(h, function(S) {
      return S;
    }) || [];
  }, only: function(h) {
    if (!Ae(h)) throw Error("React.Children.only expected to receive a single React element child.");
    return h;
  } }, Q.Component = V, Q.Fragment = c, Q.Profiler = x, Q.PureComponent = Ee, Q.StrictMode = y, Q.Suspense = R, Q.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED = F, Q.act = P, Q.cloneElement = function(h, S, J) {
    if (h == null) throw Error("React.cloneElement(...): The argument must be a React element, but you passed " + h + ".");
    var G = ce({}, h.props), _ = h.key, b = h.ref, le = h._owner;
    if (S != null) {
      if (S.ref !== void 0 && (b = S.ref, le = fe.current), S.key !== void 0 && (_ = "" + S.key), h.type && h.type.defaultProps) var ne = h.type.defaultProps;
      for (pe in S) X.call(S, pe) && !Se.hasOwnProperty(pe) && (G[pe] = S[pe] === void 0 && ne !== void 0 ? ne[pe] : S[pe]);
    }
    var pe = arguments.length - 2;
    if (pe === 1) G.children = J;
    else if (1 < pe) {
      ne = Array(pe);
      for (var en = 0; en < pe; en++) ne[en] = arguments[en + 2];
      G.children = ne;
    }
    return { $$typeof: u, type: h.type, key: _, ref: b, props: G, _owner: le };
  }, Q.createContext = function(h) {
    return h = { $$typeof: L, _currentValue: h, _currentValue2: h, _threadCount: 0, Provider: null, Consumer: null, _defaultValue: null, _globalName: null }, h.Provider = { $$typeof: E, _context: h }, h.Consumer = h;
  }, Q.createElement = ye, Q.createFactory = function(h) {
    var S = ye.bind(null, h);
    return S.type = h, S;
  }, Q.createRef = function() {
    return { current: null };
  }, Q.forwardRef = function(h) {
    return { $$typeof: T, render: h };
  }, Q.isValidElement = Ae, Q.lazy = function(h) {
    return { $$typeof: B, _payload: { _status: -1, _result: h }, _init: Oe };
  }, Q.memo = function(h, S) {
    return { $$typeof: w, type: h, compare: S === void 0 ? null : S };
  }, Q.startTransition = function(h) {
    var S = k.transition;
    k.transition = {};
    try {
      h();
    } finally {
      k.transition = S;
    }
  }, Q.unstable_act = P, Q.useCallback = function(h, S) {
    return se.current.useCallback(h, S);
  }, Q.useContext = function(h) {
    return se.current.useContext(h);
  }, Q.useDebugValue = function() {
  }, Q.useDeferredValue = function(h) {
    return se.current.useDeferredValue(h);
  }, Q.useEffect = function(h, S) {
    return se.current.useEffect(h, S);
  }, Q.useId = function() {
    return se.current.useId();
  }, Q.useImperativeHandle = function(h, S, J) {
    return se.current.useImperativeHandle(h, S, J);
  }, Q.useInsertionEffect = function(h, S) {
    return se.current.useInsertionEffect(h, S);
  }, Q.useLayoutEffect = function(h, S) {
    return se.current.useLayoutEffect(h, S);
  }, Q.useMemo = function(h, S) {
    return se.current.useMemo(h, S);
  }, Q.useReducer = function(h, S, J) {
    return se.current.useReducer(h, S, J);
  }, Q.useRef = function(h) {
    return se.current.useRef(h);
  }, Q.useState = function(h) {
    return se.current.useState(h);
  }, Q.useSyncExternalStore = function(h, S, J) {
    return se.current.useSyncExternalStore(h, S, J);
  }, Q.useTransition = function() {
    return se.current.useTransition();
  }, Q.version = "18.3.1", Q;
}
var qa;
function Xo() {
  return qa || (qa = 1, Vo.exports = uf()), Vo.exports;
}
/**
 * @license React
 * react-jsx-runtime.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var Aa;
function af() {
  if (Aa) return Er;
  Aa = 1;
  var u = Xo(), a = Symbol.for("react.element"), c = Symbol.for("react.fragment"), y = Object.prototype.hasOwnProperty, x = u.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED.ReactCurrentOwner, E = { key: !0, ref: !0, __self: !0, __source: !0 };
  function L(T, R, w) {
    var B, A = {}, Z = null, oe = null;
    w !== void 0 && (Z = "" + w), R.key !== void 0 && (Z = "" + R.key), R.ref !== void 0 && (oe = R.ref);
    for (B in R) y.call(R, B) && !E.hasOwnProperty(B) && (A[B] = R[B]);
    if (T && T.defaultProps) for (B in R = T.defaultProps, R) A[B] === void 0 && (A[B] = R[B]);
    return { $$typeof: a, type: T, key: Z, ref: oe, props: A, _owner: x.current };
  }
  return Er.Fragment = c, Er.jsx = L, Er.jsxs = L, Er;
}
var Ba;
function cf() {
  return Ba || (Ba = 1, Do.exports = af()), Do.exports;
}
var s = cf(), ge = Xo(), Vl = {}, Uo = { exports: {} }, _e = {}, Ho = { exports: {} }, qo = {};
/**
 * @license React
 * scheduler.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var Xa;
function df() {
  return Xa || (Xa = 1, (function(u) {
    function a(k, F) {
      var P = k.length;
      k.push(F);
      e: for (; 0 < P; ) {
        var h = P - 1 >>> 1, S = k[h];
        if (0 < x(S, F)) k[h] = F, k[P] = S, P = h;
        else break e;
      }
    }
    function c(k) {
      return k.length === 0 ? null : k[0];
    }
    function y(k) {
      if (k.length === 0) return null;
      var F = k[0], P = k.pop();
      if (P !== F) {
        k[0] = P;
        e: for (var h = 0, S = k.length, J = S >>> 1; h < J; ) {
          var G = 2 * (h + 1) - 1, _ = k[G], b = G + 1, le = k[b];
          if (0 > x(_, P)) b < S && 0 > x(le, _) ? (k[h] = le, k[b] = P, h = b) : (k[h] = _, k[G] = P, h = G);
          else if (b < S && 0 > x(le, P)) k[h] = le, k[b] = P, h = b;
          else break e;
        }
      }
      return F;
    }
    function x(k, F) {
      var P = k.sortIndex - F.sortIndex;
      return P !== 0 ? P : k.id - F.id;
    }
    if (typeof performance == "object" && typeof performance.now == "function") {
      var E = performance;
      u.unstable_now = function() {
        return E.now();
      };
    } else {
      var L = Date, T = L.now();
      u.unstable_now = function() {
        return L.now() - T;
      };
    }
    var R = [], w = [], B = 1, A = null, Z = 3, oe = !1, ce = !1, K = !1, V = typeof setTimeout == "function" ? setTimeout : null, re = typeof clearTimeout == "function" ? clearTimeout : null, Ee = typeof setImmediate < "u" ? setImmediate : null;
    typeof navigator < "u" && navigator.scheduling !== void 0 && navigator.scheduling.isInputPending !== void 0 && navigator.scheduling.isInputPending.bind(navigator.scheduling);
    function Ne(k) {
      for (var F = c(w); F !== null; ) {
        if (F.callback === null) y(w);
        else if (F.startTime <= k) y(w), F.sortIndex = F.expirationTime, a(R, F);
        else break;
        F = c(w);
      }
    }
    function de(k) {
      if (K = !1, Ne(k), !ce) if (c(R) !== null) ce = !0, Oe(X);
      else {
        var F = c(w);
        F !== null && se(de, F.startTime - k);
      }
    }
    function X(k, F) {
      ce = !1, K && (K = !1, re(ye), ye = -1), oe = !0;
      var P = Z;
      try {
        for (Ne(F), A = c(R); A !== null && (!(A.expirationTime > F) || k && !$e()); ) {
          var h = A.callback;
          if (typeof h == "function") {
            A.callback = null, Z = A.priorityLevel;
            var S = h(A.expirationTime <= F);
            F = u.unstable_now(), typeof S == "function" ? A.callback = S : A === c(R) && y(R), Ne(F);
          } else y(R);
          A = c(R);
        }
        if (A !== null) var J = !0;
        else {
          var G = c(w);
          G !== null && se(de, G.startTime - F), J = !1;
        }
        return J;
      } finally {
        A = null, Z = P, oe = !1;
      }
    }
    var fe = !1, Se = null, ye = -1, Ze = 5, Ae = -1;
    function $e() {
      return !(u.unstable_now() - Ae < Ze);
    }
    function We() {
      if (Se !== null) {
        var k = u.unstable_now();
        Ae = k;
        var F = !0;
        try {
          F = Se(!0, k);
        } finally {
          F ? ee() : (fe = !1, Se = null);
        }
      } else fe = !1;
    }
    var ee;
    if (typeof Ee == "function") ee = function() {
      Ee(We);
    };
    else if (typeof MessageChannel < "u") {
      var ze = new MessageChannel(), De = ze.port2;
      ze.port1.onmessage = We, ee = function() {
        De.postMessage(null);
      };
    } else ee = function() {
      V(We, 0);
    };
    function Oe(k) {
      Se = k, fe || (fe = !0, ee());
    }
    function se(k, F) {
      ye = V(function() {
        k(u.unstable_now());
      }, F);
    }
    u.unstable_IdlePriority = 5, u.unstable_ImmediatePriority = 1, u.unstable_LowPriority = 4, u.unstable_NormalPriority = 3, u.unstable_Profiling = null, u.unstable_UserBlockingPriority = 2, u.unstable_cancelCallback = function(k) {
      k.callback = null;
    }, u.unstable_continueExecution = function() {
      ce || oe || (ce = !0, Oe(X));
    }, u.unstable_forceFrameRate = function(k) {
      0 > k || 125 < k ? console.error("forceFrameRate takes a positive int between 0 and 125, forcing frame rates higher than 125 fps is not supported") : Ze = 0 < k ? Math.floor(1e3 / k) : 5;
    }, u.unstable_getCurrentPriorityLevel = function() {
      return Z;
    }, u.unstable_getFirstCallbackNode = function() {
      return c(R);
    }, u.unstable_next = function(k) {
      switch (Z) {
        case 1:
        case 2:
        case 3:
          var F = 3;
          break;
        default:
          F = Z;
      }
      var P = Z;
      Z = F;
      try {
        return k();
      } finally {
        Z = P;
      }
    }, u.unstable_pauseExecution = function() {
    }, u.unstable_requestPaint = function() {
    }, u.unstable_runWithPriority = function(k, F) {
      switch (k) {
        case 1:
        case 2:
        case 3:
        case 4:
        case 5:
          break;
        default:
          k = 3;
      }
      var P = Z;
      Z = k;
      try {
        return F();
      } finally {
        Z = P;
      }
    }, u.unstable_scheduleCallback = function(k, F, P) {
      var h = u.unstable_now();
      switch (typeof P == "object" && P !== null ? (P = P.delay, P = typeof P == "number" && 0 < P ? h + P : h) : P = h, k) {
        case 1:
          var S = -1;
          break;
        case 2:
          S = 250;
          break;
        case 5:
          S = 1073741823;
          break;
        case 4:
          S = 1e4;
          break;
        default:
          S = 5e3;
      }
      return S = P + S, k = { id: B++, callback: F, priorityLevel: k, startTime: P, expirationTime: S, sortIndex: -1 }, P > h ? (k.sortIndex = P, a(w, k), c(R) === null && k === c(w) && (K ? (re(ye), ye = -1) : K = !0, se(de, P - h))) : (k.sortIndex = S, a(R, k), ce || oe || (ce = !0, Oe(X))), k;
    }, u.unstable_shouldYield = $e, u.unstable_wrapCallback = function(k) {
      var F = Z;
      return function() {
        var P = Z;
        Z = F;
        try {
          return k.apply(this, arguments);
        } finally {
          Z = P;
        }
      };
    };
  })(qo)), qo;
}
var Za;
function ff() {
  return Za || (Za = 1, Ho.exports = df()), Ho.exports;
}
/**
 * @license React
 * react-dom.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var Ja;
function pf() {
  if (Ja) return _e;
  Ja = 1;
  var u = Xo(), a = ff();
  function c(e) {
    for (var n = "https://reactjs.org/docs/error-decoder.html?invariant=" + e, t = 1; t < arguments.length; t++) n += "&args[]=" + encodeURIComponent(arguments[t]);
    return "Minified React error #" + e + "; visit " + n + " for the full message or use the non-minified dev environment for full errors and additional helpful warnings.";
  }
  var y = /* @__PURE__ */ new Set(), x = {};
  function E(e, n) {
    L(e, n), L(e + "Capture", n);
  }
  function L(e, n) {
    for (x[e] = n, e = 0; e < n.length; e++) y.add(n[e]);
  }
  var T = !(typeof window > "u" || typeof window.document > "u" || typeof window.document.createElement > "u"), R = Object.prototype.hasOwnProperty, w = /^[:A-Z_a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD][:A-Z_a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD\-.0-9\u00B7\u0300-\u036F\u203F-\u2040]*$/, B = {}, A = {};
  function Z(e) {
    return R.call(A, e) ? !0 : R.call(B, e) ? !1 : w.test(e) ? A[e] = !0 : (B[e] = !0, !1);
  }
  function oe(e, n, t, r) {
    if (t !== null && t.type === 0) return !1;
    switch (typeof n) {
      case "function":
      case "symbol":
        return !0;
      case "boolean":
        return r ? !1 : t !== null ? !t.acceptsBooleans : (e = e.toLowerCase().slice(0, 5), e !== "data-" && e !== "aria-");
      default:
        return !1;
    }
  }
  function ce(e, n, t, r) {
    if (n === null || typeof n > "u" || oe(e, n, t, r)) return !0;
    if (r) return !1;
    if (t !== null) switch (t.type) {
      case 3:
        return !n;
      case 4:
        return n === !1;
      case 5:
        return isNaN(n);
      case 6:
        return isNaN(n) || 1 > n;
    }
    return !1;
  }
  function K(e, n, t, r, l, i, o) {
    this.acceptsBooleans = n === 2 || n === 3 || n === 4, this.attributeName = r, this.attributeNamespace = l, this.mustUseProperty = t, this.propertyName = e, this.type = n, this.sanitizeURL = i, this.removeEmptyString = o;
  }
  var V = {};
  "children dangerouslySetInnerHTML defaultValue defaultChecked innerHTML suppressContentEditableWarning suppressHydrationWarning style".split(" ").forEach(function(e) {
    V[e] = new K(e, 0, !1, e, null, !1, !1);
  }), [["acceptCharset", "accept-charset"], ["className", "class"], ["htmlFor", "for"], ["httpEquiv", "http-equiv"]].forEach(function(e) {
    var n = e[0];
    V[n] = new K(n, 1, !1, e[1], null, !1, !1);
  }), ["contentEditable", "draggable", "spellCheck", "value"].forEach(function(e) {
    V[e] = new K(e, 2, !1, e.toLowerCase(), null, !1, !1);
  }), ["autoReverse", "externalResourcesRequired", "focusable", "preserveAlpha"].forEach(function(e) {
    V[e] = new K(e, 2, !1, e, null, !1, !1);
  }), "allowFullScreen async autoFocus autoPlay controls default defer disabled disablePictureInPicture disableRemotePlayback formNoValidate hidden loop noModule noValidate open playsInline readOnly required reversed scoped seamless itemScope".split(" ").forEach(function(e) {
    V[e] = new K(e, 3, !1, e.toLowerCase(), null, !1, !1);
  }), ["checked", "multiple", "muted", "selected"].forEach(function(e) {
    V[e] = new K(e, 3, !0, e, null, !1, !1);
  }), ["capture", "download"].forEach(function(e) {
    V[e] = new K(e, 4, !1, e, null, !1, !1);
  }), ["cols", "rows", "size", "span"].forEach(function(e) {
    V[e] = new K(e, 6, !1, e, null, !1, !1);
  }), ["rowSpan", "start"].forEach(function(e) {
    V[e] = new K(e, 5, !1, e.toLowerCase(), null, !1, !1);
  });
  var re = /[\-:]([a-z])/g;
  function Ee(e) {
    return e[1].toUpperCase();
  }
  "accent-height alignment-baseline arabic-form baseline-shift cap-height clip-path clip-rule color-interpolation color-interpolation-filters color-profile color-rendering dominant-baseline enable-background fill-opacity fill-rule flood-color flood-opacity font-family font-size font-size-adjust font-stretch font-style font-variant font-weight glyph-name glyph-orientation-horizontal glyph-orientation-vertical horiz-adv-x horiz-origin-x image-rendering letter-spacing lighting-color marker-end marker-mid marker-start overline-position overline-thickness paint-order panose-1 pointer-events rendering-intent shape-rendering stop-color stop-opacity strikethrough-position strikethrough-thickness stroke-dasharray stroke-dashoffset stroke-linecap stroke-linejoin stroke-miterlimit stroke-opacity stroke-width text-anchor text-decoration text-rendering underline-position underline-thickness unicode-bidi unicode-range units-per-em v-alphabetic v-hanging v-ideographic v-mathematical vector-effect vert-adv-y vert-origin-x vert-origin-y word-spacing writing-mode xmlns:xlink x-height".split(" ").forEach(function(e) {
    var n = e.replace(
      re,
      Ee
    );
    V[n] = new K(n, 1, !1, e, null, !1, !1);
  }), "xlink:actuate xlink:arcrole xlink:role xlink:show xlink:title xlink:type".split(" ").forEach(function(e) {
    var n = e.replace(re, Ee);
    V[n] = new K(n, 1, !1, e, "http://www.w3.org/1999/xlink", !1, !1);
  }), ["xml:base", "xml:lang", "xml:space"].forEach(function(e) {
    var n = e.replace(re, Ee);
    V[n] = new K(n, 1, !1, e, "http://www.w3.org/XML/1998/namespace", !1, !1);
  }), ["tabIndex", "crossOrigin"].forEach(function(e) {
    V[e] = new K(e, 1, !1, e.toLowerCase(), null, !1, !1);
  }), V.xlinkHref = new K("xlinkHref", 1, !1, "xlink:href", "http://www.w3.org/1999/xlink", !0, !1), ["src", "href", "action", "formAction"].forEach(function(e) {
    V[e] = new K(e, 1, !1, e.toLowerCase(), null, !0, !0);
  });
  function Ne(e, n, t, r) {
    var l = V.hasOwnProperty(n) ? V[n] : null;
    (l !== null ? l.type !== 0 : r || !(2 < n.length) || n[0] !== "o" && n[0] !== "O" || n[1] !== "n" && n[1] !== "N") && (ce(n, t, l, r) && (t = null), r || l === null ? Z(n) && (t === null ? e.removeAttribute(n) : e.setAttribute(n, "" + t)) : l.mustUseProperty ? e[l.propertyName] = t === null ? l.type === 3 ? !1 : "" : t : (n = l.attributeName, r = l.attributeNamespace, t === null ? e.removeAttribute(n) : (l = l.type, t = l === 3 || l === 4 && t === !0 ? "" : "" + t, r ? e.setAttributeNS(r, n, t) : e.setAttribute(n, t))));
  }
  var de = u.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED, X = Symbol.for("react.element"), fe = Symbol.for("react.portal"), Se = Symbol.for("react.fragment"), ye = Symbol.for("react.strict_mode"), Ze = Symbol.for("react.profiler"), Ae = Symbol.for("react.provider"), $e = Symbol.for("react.context"), We = Symbol.for("react.forward_ref"), ee = Symbol.for("react.suspense"), ze = Symbol.for("react.suspense_list"), De = Symbol.for("react.memo"), Oe = Symbol.for("react.lazy"), se = Symbol.for("react.offscreen"), k = Symbol.iterator;
  function F(e) {
    return e === null || typeof e != "object" ? null : (e = k && e[k] || e["@@iterator"], typeof e == "function" ? e : null);
  }
  var P = Object.assign, h;
  function S(e) {
    if (h === void 0) try {
      throw Error();
    } catch (t) {
      var n = t.stack.trim().match(/\n( *(at )?)/);
      h = n && n[1] || "";
    }
    return `
` + h + e;
  }
  var J = !1;
  function G(e, n) {
    if (!e || J) return "";
    J = !0;
    var t = Error.prepareStackTrace;
    Error.prepareStackTrace = void 0;
    try {
      if (n) if (n = function() {
        throw Error();
      }, Object.defineProperty(n.prototype, "props", { set: function() {
        throw Error();
      } }), typeof Reflect == "object" && Reflect.construct) {
        try {
          Reflect.construct(n, []);
        } catch (g) {
          var r = g;
        }
        Reflect.construct(e, [], n);
      } else {
        try {
          n.call();
        } catch (g) {
          r = g;
        }
        e.call(n.prototype);
      }
      else {
        try {
          throw Error();
        } catch (g) {
          r = g;
        }
        e();
      }
    } catch (g) {
      if (g && r && typeof g.stack == "string") {
        for (var l = g.stack.split(`
`), i = r.stack.split(`
`), o = l.length - 1, d = i.length - 1; 1 <= o && 0 <= d && l[o] !== i[d]; ) d--;
        for (; 1 <= o && 0 <= d; o--, d--) if (l[o] !== i[d]) {
          if (o !== 1 || d !== 1)
            do
              if (o--, d--, 0 > d || l[o] !== i[d]) {
                var f = `
` + l[o].replace(" at new ", " at ");
                return e.displayName && f.includes("<anonymous>") && (f = f.replace("<anonymous>", e.displayName)), f;
              }
            while (1 <= o && 0 <= d);
          break;
        }
      }
    } finally {
      J = !1, Error.prepareStackTrace = t;
    }
    return (e = e ? e.displayName || e.name : "") ? S(e) : "";
  }
  function _(e) {
    switch (e.tag) {
      case 5:
        return S(e.type);
      case 16:
        return S("Lazy");
      case 13:
        return S("Suspense");
      case 19:
        return S("SuspenseList");
      case 0:
      case 2:
      case 15:
        return e = G(e.type, !1), e;
      case 11:
        return e = G(e.type.render, !1), e;
      case 1:
        return e = G(e.type, !0), e;
      default:
        return "";
    }
  }
  function b(e) {
    if (e == null) return null;
    if (typeof e == "function") return e.displayName || e.name || null;
    if (typeof e == "string") return e;
    switch (e) {
      case Se:
        return "Fragment";
      case fe:
        return "Portal";
      case Ze:
        return "Profiler";
      case ye:
        return "StrictMode";
      case ee:
        return "Suspense";
      case ze:
        return "SuspenseList";
    }
    if (typeof e == "object") switch (e.$$typeof) {
      case $e:
        return (e.displayName || "Context") + ".Consumer";
      case Ae:
        return (e._context.displayName || "Context") + ".Provider";
      case We:
        var n = e.render;
        return e = e.displayName, e || (e = n.displayName || n.name || "", e = e !== "" ? "ForwardRef(" + e + ")" : "ForwardRef"), e;
      case De:
        return n = e.displayName || null, n !== null ? n : b(e.type) || "Memo";
      case Oe:
        n = e._payload, e = e._init;
        try {
          return b(e(n));
        } catch {
        }
    }
    return null;
  }
  function le(e) {
    var n = e.type;
    switch (e.tag) {
      case 24:
        return "Cache";
      case 9:
        return (n.displayName || "Context") + ".Consumer";
      case 10:
        return (n._context.displayName || "Context") + ".Provider";
      case 18:
        return "DehydratedFragment";
      case 11:
        return e = n.render, e = e.displayName || e.name || "", n.displayName || (e !== "" ? "ForwardRef(" + e + ")" : "ForwardRef");
      case 7:
        return "Fragment";
      case 5:
        return n;
      case 4:
        return "Portal";
      case 3:
        return "Root";
      case 6:
        return "Text";
      case 16:
        return b(n);
      case 8:
        return n === ye ? "StrictMode" : "Mode";
      case 22:
        return "Offscreen";
      case 12:
        return "Profiler";
      case 21:
        return "Scope";
      case 13:
        return "Suspense";
      case 19:
        return "SuspenseList";
      case 25:
        return "TracingMarker";
      case 1:
      case 0:
      case 17:
      case 2:
      case 14:
      case 15:
        if (typeof n == "function") return n.displayName || n.name || null;
        if (typeof n == "string") return n;
    }
    return null;
  }
  function ne(e) {
    switch (typeof e) {
      case "boolean":
      case "number":
      case "string":
      case "undefined":
        return e;
      case "object":
        return e;
      default:
        return "";
    }
  }
  function pe(e) {
    var n = e.type;
    return (e = e.nodeName) && e.toLowerCase() === "input" && (n === "checkbox" || n === "radio");
  }
  function en(e) {
    var n = pe(e) ? "checked" : "value", t = Object.getOwnPropertyDescriptor(e.constructor.prototype, n), r = "" + e[n];
    if (!e.hasOwnProperty(n) && typeof t < "u" && typeof t.get == "function" && typeof t.set == "function") {
      var l = t.get, i = t.set;
      return Object.defineProperty(e, n, { configurable: !0, get: function() {
        return l.call(this);
      }, set: function(o) {
        r = "" + o, i.call(this, o);
      } }), Object.defineProperty(e, n, { enumerable: t.enumerable }), { getValue: function() {
        return r;
      }, setValue: function(o) {
        r = "" + o;
      }, stopTracking: function() {
        e._valueTracker = null, delete e[n];
      } };
    }
  }
  function Rr(e) {
    e._valueTracker || (e._valueTracker = en(e));
  }
  function Jo(e) {
    if (!e) return !1;
    var n = e._valueTracker;
    if (!n) return !0;
    var t = n.getValue(), r = "";
    return e && (r = pe(e) ? e.checked ? "true" : "false" : e.value), e = r, e !== t ? (n.setValue(e), !0) : !1;
  }
  function Pr(e) {
    if (e = e || (typeof document < "u" ? document : void 0), typeof e > "u") return null;
    try {
      return e.activeElement || e.body;
    } catch {
      return e.body;
    }
  }
  function Bl(e, n) {
    var t = n.checked;
    return P({}, n, { defaultChecked: void 0, defaultValue: void 0, value: void 0, checked: t ?? e._wrapperState.initialChecked });
  }
  function Ko(e, n) {
    var t = n.defaultValue == null ? "" : n.defaultValue, r = n.checked != null ? n.checked : n.defaultChecked;
    t = ne(n.value != null ? n.value : t), e._wrapperState = { initialChecked: r, initialValue: t, controlled: n.type === "checkbox" || n.type === "radio" ? n.checked != null : n.value != null };
  }
  function Qo(e, n) {
    n = n.checked, n != null && Ne(e, "checked", n, !1);
  }
  function Xl(e, n) {
    Qo(e, n);
    var t = ne(n.value), r = n.type;
    if (t != null) r === "number" ? (t === 0 && e.value === "" || e.value != t) && (e.value = "" + t) : e.value !== "" + t && (e.value = "" + t);
    else if (r === "submit" || r === "reset") {
      e.removeAttribute("value");
      return;
    }
    n.hasOwnProperty("value") ? Zl(e, n.type, t) : n.hasOwnProperty("defaultValue") && Zl(e, n.type, ne(n.defaultValue)), n.checked == null && n.defaultChecked != null && (e.defaultChecked = !!n.defaultChecked);
  }
  function Go(e, n, t) {
    if (n.hasOwnProperty("value") || n.hasOwnProperty("defaultValue")) {
      var r = n.type;
      if (!(r !== "submit" && r !== "reset" || n.value !== void 0 && n.value !== null)) return;
      n = "" + e._wrapperState.initialValue, t || n === e.value || (e.value = n), e.defaultValue = n;
    }
    t = e.name, t !== "" && (e.name = ""), e.defaultChecked = !!e._wrapperState.initialChecked, t !== "" && (e.name = t);
  }
  function Zl(e, n, t) {
    (n !== "number" || Pr(e.ownerDocument) !== e) && (t == null ? e.defaultValue = "" + e._wrapperState.initialValue : e.defaultValue !== "" + t && (e.defaultValue = "" + t));
  }
  var Ut = Array.isArray;
  function ht(e, n, t, r) {
    if (e = e.options, n) {
      n = {};
      for (var l = 0; l < t.length; l++) n["$" + t[l]] = !0;
      for (t = 0; t < e.length; t++) l = n.hasOwnProperty("$" + e[t].value), e[t].selected !== l && (e[t].selected = l), l && r && (e[t].defaultSelected = !0);
    } else {
      for (t = "" + ne(t), n = null, l = 0; l < e.length; l++) {
        if (e[l].value === t) {
          e[l].selected = !0, r && (e[l].defaultSelected = !0);
          return;
        }
        n !== null || e[l].disabled || (n = e[l]);
      }
      n !== null && (n.selected = !0);
    }
  }
  function Jl(e, n) {
    if (n.dangerouslySetInnerHTML != null) throw Error(c(91));
    return P({}, n, { value: void 0, defaultValue: void 0, children: "" + e._wrapperState.initialValue });
  }
  function Yo(e, n) {
    var t = n.value;
    if (t == null) {
      if (t = n.children, n = n.defaultValue, t != null) {
        if (n != null) throw Error(c(92));
        if (Ut(t)) {
          if (1 < t.length) throw Error(c(93));
          t = t[0];
        }
        n = t;
      }
      n == null && (n = ""), t = n;
    }
    e._wrapperState = { initialValue: ne(t) };
  }
  function _o(e, n) {
    var t = ne(n.value), r = ne(n.defaultValue);
    t != null && (t = "" + t, t !== e.value && (e.value = t), n.defaultValue == null && e.defaultValue !== t && (e.defaultValue = t)), r != null && (e.defaultValue = "" + r);
  }
  function bo(e) {
    var n = e.textContent;
    n === e._wrapperState.initialValue && n !== "" && n !== null && (e.value = n);
  }
  function $o(e) {
    switch (e) {
      case "svg":
        return "http://www.w3.org/2000/svg";
      case "math":
        return "http://www.w3.org/1998/Math/MathML";
      default:
        return "http://www.w3.org/1999/xhtml";
    }
  }
  function Kl(e, n) {
    return e == null || e === "http://www.w3.org/1999/xhtml" ? $o(n) : e === "http://www.w3.org/2000/svg" && n === "foreignObject" ? "http://www.w3.org/1999/xhtml" : e;
  }
  var Tr, es = (function(e) {
    return typeof MSApp < "u" && MSApp.execUnsafeLocalFunction ? function(n, t, r, l) {
      MSApp.execUnsafeLocalFunction(function() {
        return e(n, t, r, l);
      });
    } : e;
  })(function(e, n) {
    if (e.namespaceURI !== "http://www.w3.org/2000/svg" || "innerHTML" in e) e.innerHTML = n;
    else {
      for (Tr = Tr || document.createElement("div"), Tr.innerHTML = "<svg>" + n.valueOf().toString() + "</svg>", n = Tr.firstChild; e.firstChild; ) e.removeChild(e.firstChild);
      for (; n.firstChild; ) e.appendChild(n.firstChild);
    }
  });
  function Ht(e, n) {
    if (n) {
      var t = e.firstChild;
      if (t && t === e.lastChild && t.nodeType === 3) {
        t.nodeValue = n;
        return;
      }
    }
    e.textContent = n;
  }
  var qt = {
    animationIterationCount: !0,
    aspectRatio: !0,
    borderImageOutset: !0,
    borderImageSlice: !0,
    borderImageWidth: !0,
    boxFlex: !0,
    boxFlexGroup: !0,
    boxOrdinalGroup: !0,
    columnCount: !0,
    columns: !0,
    flex: !0,
    flexGrow: !0,
    flexPositive: !0,
    flexShrink: !0,
    flexNegative: !0,
    flexOrder: !0,
    gridArea: !0,
    gridRow: !0,
    gridRowEnd: !0,
    gridRowSpan: !0,
    gridRowStart: !0,
    gridColumn: !0,
    gridColumnEnd: !0,
    gridColumnSpan: !0,
    gridColumnStart: !0,
    fontWeight: !0,
    lineClamp: !0,
    lineHeight: !0,
    opacity: !0,
    order: !0,
    orphans: !0,
    tabSize: !0,
    widows: !0,
    zIndex: !0,
    zoom: !0,
    fillOpacity: !0,
    floodOpacity: !0,
    stopOpacity: !0,
    strokeDasharray: !0,
    strokeDashoffset: !0,
    strokeMiterlimit: !0,
    strokeOpacity: !0,
    strokeWidth: !0
  }, dc = ["Webkit", "ms", "Moz", "O"];
  Object.keys(qt).forEach(function(e) {
    dc.forEach(function(n) {
      n = n + e.charAt(0).toUpperCase() + e.substring(1), qt[n] = qt[e];
    });
  });
  function ns(e, n, t) {
    return n == null || typeof n == "boolean" || n === "" ? "" : t || typeof n != "number" || n === 0 || qt.hasOwnProperty(e) && qt[e] ? ("" + n).trim() : n + "px";
  }
  function ts(e, n) {
    e = e.style;
    for (var t in n) if (n.hasOwnProperty(t)) {
      var r = t.indexOf("--") === 0, l = ns(t, n[t], r);
      t === "float" && (t = "cssFloat"), r ? e.setProperty(t, l) : e[t] = l;
    }
  }
  var fc = P({ menuitem: !0 }, { area: !0, base: !0, br: !0, col: !0, embed: !0, hr: !0, img: !0, input: !0, keygen: !0, link: !0, meta: !0, param: !0, source: !0, track: !0, wbr: !0 });
  function Ql(e, n) {
    if (n) {
      if (fc[e] && (n.children != null || n.dangerouslySetInnerHTML != null)) throw Error(c(137, e));
      if (n.dangerouslySetInnerHTML != null) {
        if (n.children != null) throw Error(c(60));
        if (typeof n.dangerouslySetInnerHTML != "object" || !("__html" in n.dangerouslySetInnerHTML)) throw Error(c(61));
      }
      if (n.style != null && typeof n.style != "object") throw Error(c(62));
    }
  }
  function Gl(e, n) {
    if (e.indexOf("-") === -1) return typeof n.is == "string";
    switch (e) {
      case "annotation-xml":
      case "color-profile":
      case "font-face":
      case "font-face-src":
      case "font-face-uri":
      case "font-face-format":
      case "font-face-name":
      case "missing-glyph":
        return !1;
      default:
        return !0;
    }
  }
  var Yl = null;
  function _l(e) {
    return e = e.target || e.srcElement || window, e.correspondingUseElement && (e = e.correspondingUseElement), e.nodeType === 3 ? e.parentNode : e;
  }
  var bl = null, mt = null, vt = null;
  function rs(e) {
    if (e = ar(e)) {
      if (typeof bl != "function") throw Error(c(280));
      var n = e.stateNode;
      n && (n = $r(n), bl(e.stateNode, e.type, n));
    }
  }
  function ls(e) {
    mt ? vt ? vt.push(e) : vt = [e] : mt = e;
  }
  function is() {
    if (mt) {
      var e = mt, n = vt;
      if (vt = mt = null, rs(e), n) for (e = 0; e < n.length; e++) rs(n[e]);
    }
  }
  function os(e, n) {
    return e(n);
  }
  function ss() {
  }
  var $l = !1;
  function us(e, n, t) {
    if ($l) return e(n, t);
    $l = !0;
    try {
      return os(e, n, t);
    } finally {
      $l = !1, (mt !== null || vt !== null) && (ss(), is());
    }
  }
  function At(e, n) {
    var t = e.stateNode;
    if (t === null) return null;
    var r = $r(t);
    if (r === null) return null;
    t = r[n];
    e: switch (n) {
      case "onClick":
      case "onClickCapture":
      case "onDoubleClick":
      case "onDoubleClickCapture":
      case "onMouseDown":
      case "onMouseDownCapture":
      case "onMouseMove":
      case "onMouseMoveCapture":
      case "onMouseUp":
      case "onMouseUpCapture":
      case "onMouseEnter":
        (r = !r.disabled) || (e = e.type, r = !(e === "button" || e === "input" || e === "select" || e === "textarea")), e = !r;
        break e;
      default:
        e = !1;
    }
    if (e) return null;
    if (t && typeof t != "function") throw Error(c(231, n, typeof t));
    return t;
  }
  var ei = !1;
  if (T) try {
    var Bt = {};
    Object.defineProperty(Bt, "passive", { get: function() {
      ei = !0;
    } }), window.addEventListener("test", Bt, Bt), window.removeEventListener("test", Bt, Bt);
  } catch {
    ei = !1;
  }
  function pc(e, n, t, r, l, i, o, d, f) {
    var g = Array.prototype.slice.call(arguments, 3);
    try {
      n.apply(t, g);
    } catch (N) {
      this.onError(N);
    }
  }
  var Xt = !1, Lr = null, Or = !1, ni = null, hc = { onError: function(e) {
    Xt = !0, Lr = e;
  } };
  function mc(e, n, t, r, l, i, o, d, f) {
    Xt = !1, Lr = null, pc.apply(hc, arguments);
  }
  function vc(e, n, t, r, l, i, o, d, f) {
    if (mc.apply(this, arguments), Xt) {
      if (Xt) {
        var g = Lr;
        Xt = !1, Lr = null;
      } else throw Error(c(198));
      Or || (Or = !0, ni = g);
    }
  }
  function et(e) {
    var n = e, t = e;
    if (e.alternate) for (; n.return; ) n = n.return;
    else {
      e = n;
      do
        n = e, (n.flags & 4098) !== 0 && (t = n.return), e = n.return;
      while (e);
    }
    return n.tag === 3 ? t : null;
  }
  function as(e) {
    if (e.tag === 13) {
      var n = e.memoizedState;
      if (n === null && (e = e.alternate, e !== null && (n = e.memoizedState)), n !== null) return n.dehydrated;
    }
    return null;
  }
  function cs(e) {
    if (et(e) !== e) throw Error(c(188));
  }
  function gc(e) {
    var n = e.alternate;
    if (!n) {
      if (n = et(e), n === null) throw Error(c(188));
      return n !== e ? null : e;
    }
    for (var t = e, r = n; ; ) {
      var l = t.return;
      if (l === null) break;
      var i = l.alternate;
      if (i === null) {
        if (r = l.return, r !== null) {
          t = r;
          continue;
        }
        break;
      }
      if (l.child === i.child) {
        for (i = l.child; i; ) {
          if (i === t) return cs(l), e;
          if (i === r) return cs(l), n;
          i = i.sibling;
        }
        throw Error(c(188));
      }
      if (t.return !== r.return) t = l, r = i;
      else {
        for (var o = !1, d = l.child; d; ) {
          if (d === t) {
            o = !0, t = l, r = i;
            break;
          }
          if (d === r) {
            o = !0, r = l, t = i;
            break;
          }
          d = d.sibling;
        }
        if (!o) {
          for (d = i.child; d; ) {
            if (d === t) {
              o = !0, t = i, r = l;
              break;
            }
            if (d === r) {
              o = !0, r = i, t = l;
              break;
            }
            d = d.sibling;
          }
          if (!o) throw Error(c(189));
        }
      }
      if (t.alternate !== r) throw Error(c(190));
    }
    if (t.tag !== 3) throw Error(c(188));
    return t.stateNode.current === t ? e : n;
  }
  function ds(e) {
    return e = gc(e), e !== null ? fs(e) : null;
  }
  function fs(e) {
    if (e.tag === 5 || e.tag === 6) return e;
    for (e = e.child; e !== null; ) {
      var n = fs(e);
      if (n !== null) return n;
      e = e.sibling;
    }
    return null;
  }
  var ps = a.unstable_scheduleCallback, hs = a.unstable_cancelCallback, yc = a.unstable_shouldYield, xc = a.unstable_requestPaint, we = a.unstable_now, wc = a.unstable_getCurrentPriorityLevel, ti = a.unstable_ImmediatePriority, ms = a.unstable_UserBlockingPriority, Fr = a.unstable_NormalPriority, kc = a.unstable_LowPriority, vs = a.unstable_IdlePriority, Mr = null, Sn = null;
  function Sc(e) {
    if (Sn && typeof Sn.onCommitFiberRoot == "function") try {
      Sn.onCommitFiberRoot(Mr, e, void 0, (e.current.flags & 128) === 128);
    } catch {
    }
  }
  var pn = Math.clz32 ? Math.clz32 : Nc, jc = Math.log, Ec = Math.LN2;
  function Nc(e) {
    return e >>>= 0, e === 0 ? 32 : 31 - (jc(e) / Ec | 0) | 0;
  }
  var Ir = 64, Wr = 4194304;
  function Zt(e) {
    switch (e & -e) {
      case 1:
        return 1;
      case 2:
        return 2;
      case 4:
        return 4;
      case 8:
        return 8;
      case 16:
        return 16;
      case 32:
        return 32;
      case 64:
      case 128:
      case 256:
      case 512:
      case 1024:
      case 2048:
      case 4096:
      case 8192:
      case 16384:
      case 32768:
      case 65536:
      case 131072:
      case 262144:
      case 524288:
      case 1048576:
      case 2097152:
        return e & 4194240;
      case 4194304:
      case 8388608:
      case 16777216:
      case 33554432:
      case 67108864:
        return e & 130023424;
      case 134217728:
        return 134217728;
      case 268435456:
        return 268435456;
      case 536870912:
        return 536870912;
      case 1073741824:
        return 1073741824;
      default:
        return e;
    }
  }
  function Dr(e, n) {
    var t = e.pendingLanes;
    if (t === 0) return 0;
    var r = 0, l = e.suspendedLanes, i = e.pingedLanes, o = t & 268435455;
    if (o !== 0) {
      var d = o & ~l;
      d !== 0 ? r = Zt(d) : (i &= o, i !== 0 && (r = Zt(i)));
    } else o = t & ~l, o !== 0 ? r = Zt(o) : i !== 0 && (r = Zt(i));
    if (r === 0) return 0;
    if (n !== 0 && n !== r && (n & l) === 0 && (l = r & -r, i = n & -n, l >= i || l === 16 && (i & 4194240) !== 0)) return n;
    if ((r & 4) !== 0 && (r |= t & 16), n = e.entangledLanes, n !== 0) for (e = e.entanglements, n &= r; 0 < n; ) t = 31 - pn(n), l = 1 << t, r |= e[t], n &= ~l;
    return r;
  }
  function zc(e, n) {
    switch (e) {
      case 1:
      case 2:
      case 4:
        return n + 250;
      case 8:
      case 16:
      case 32:
      case 64:
      case 128:
      case 256:
      case 512:
      case 1024:
      case 2048:
      case 4096:
      case 8192:
      case 16384:
      case 32768:
      case 65536:
      case 131072:
      case 262144:
      case 524288:
      case 1048576:
      case 2097152:
        return n + 5e3;
      case 4194304:
      case 8388608:
      case 16777216:
      case 33554432:
      case 67108864:
        return -1;
      case 134217728:
      case 268435456:
      case 536870912:
      case 1073741824:
        return -1;
      default:
        return -1;
    }
  }
  function Cc(e, n) {
    for (var t = e.suspendedLanes, r = e.pingedLanes, l = e.expirationTimes, i = e.pendingLanes; 0 < i; ) {
      var o = 31 - pn(i), d = 1 << o, f = l[o];
      f === -1 ? ((d & t) === 0 || (d & r) !== 0) && (l[o] = zc(d, n)) : f <= n && (e.expiredLanes |= d), i &= ~d;
    }
  }
  function ri(e) {
    return e = e.pendingLanes & -1073741825, e !== 0 ? e : e & 1073741824 ? 1073741824 : 0;
  }
  function gs() {
    var e = Ir;
    return Ir <<= 1, (Ir & 4194240) === 0 && (Ir = 64), e;
  }
  function li(e) {
    for (var n = [], t = 0; 31 > t; t++) n.push(e);
    return n;
  }
  function Jt(e, n, t) {
    e.pendingLanes |= n, n !== 536870912 && (e.suspendedLanes = 0, e.pingedLanes = 0), e = e.eventTimes, n = 31 - pn(n), e[n] = t;
  }
  function Rc(e, n) {
    var t = e.pendingLanes & ~n;
    e.pendingLanes = n, e.suspendedLanes = 0, e.pingedLanes = 0, e.expiredLanes &= n, e.mutableReadLanes &= n, e.entangledLanes &= n, n = e.entanglements;
    var r = e.eventTimes;
    for (e = e.expirationTimes; 0 < t; ) {
      var l = 31 - pn(t), i = 1 << l;
      n[l] = 0, r[l] = -1, e[l] = -1, t &= ~i;
    }
  }
  function ii(e, n) {
    var t = e.entangledLanes |= n;
    for (e = e.entanglements; t; ) {
      var r = 31 - pn(t), l = 1 << r;
      l & n | e[r] & n && (e[r] |= n), t &= ~l;
    }
  }
  var te = 0;
  function ys(e) {
    return e &= -e, 1 < e ? 4 < e ? (e & 268435455) !== 0 ? 16 : 536870912 : 4 : 1;
  }
  var xs, oi, ws, ks, Ss, si = !1, Vr = [], In = null, Wn = null, Dn = null, Kt = /* @__PURE__ */ new Map(), Qt = /* @__PURE__ */ new Map(), Vn = [], Pc = "mousedown mouseup touchcancel touchend touchstart auxclick dblclick pointercancel pointerdown pointerup dragend dragstart drop compositionend compositionstart keydown keypress keyup input textInput copy cut paste click change contextmenu reset submit".split(" ");
  function js(e, n) {
    switch (e) {
      case "focusin":
      case "focusout":
        In = null;
        break;
      case "dragenter":
      case "dragleave":
        Wn = null;
        break;
      case "mouseover":
      case "mouseout":
        Dn = null;
        break;
      case "pointerover":
      case "pointerout":
        Kt.delete(n.pointerId);
        break;
      case "gotpointercapture":
      case "lostpointercapture":
        Qt.delete(n.pointerId);
    }
  }
  function Gt(e, n, t, r, l, i) {
    return e === null || e.nativeEvent !== i ? (e = { blockedOn: n, domEventName: t, eventSystemFlags: r, nativeEvent: i, targetContainers: [l] }, n !== null && (n = ar(n), n !== null && oi(n)), e) : (e.eventSystemFlags |= r, n = e.targetContainers, l !== null && n.indexOf(l) === -1 && n.push(l), e);
  }
  function Tc(e, n, t, r, l) {
    switch (n) {
      case "focusin":
        return In = Gt(In, e, n, t, r, l), !0;
      case "dragenter":
        return Wn = Gt(Wn, e, n, t, r, l), !0;
      case "mouseover":
        return Dn = Gt(Dn, e, n, t, r, l), !0;
      case "pointerover":
        var i = l.pointerId;
        return Kt.set(i, Gt(Kt.get(i) || null, e, n, t, r, l)), !0;
      case "gotpointercapture":
        return i = l.pointerId, Qt.set(i, Gt(Qt.get(i) || null, e, n, t, r, l)), !0;
    }
    return !1;
  }
  function Es(e) {
    var n = nt(e.target);
    if (n !== null) {
      var t = et(n);
      if (t !== null) {
        if (n = t.tag, n === 13) {
          if (n = as(t), n !== null) {
            e.blockedOn = n, Ss(e.priority, function() {
              ws(t);
            });
            return;
          }
        } else if (n === 3 && t.stateNode.current.memoizedState.isDehydrated) {
          e.blockedOn = t.tag === 3 ? t.stateNode.containerInfo : null;
          return;
        }
      }
    }
    e.blockedOn = null;
  }
  function Ur(e) {
    if (e.blockedOn !== null) return !1;
    for (var n = e.targetContainers; 0 < n.length; ) {
      var t = ai(e.domEventName, e.eventSystemFlags, n[0], e.nativeEvent);
      if (t === null) {
        t = e.nativeEvent;
        var r = new t.constructor(t.type, t);
        Yl = r, t.target.dispatchEvent(r), Yl = null;
      } else return n = ar(t), n !== null && oi(n), e.blockedOn = t, !1;
      n.shift();
    }
    return !0;
  }
  function Ns(e, n, t) {
    Ur(e) && t.delete(n);
  }
  function Lc() {
    si = !1, In !== null && Ur(In) && (In = null), Wn !== null && Ur(Wn) && (Wn = null), Dn !== null && Ur(Dn) && (Dn = null), Kt.forEach(Ns), Qt.forEach(Ns);
  }
  function Yt(e, n) {
    e.blockedOn === n && (e.blockedOn = null, si || (si = !0, a.unstable_scheduleCallback(a.unstable_NormalPriority, Lc)));
  }
  function _t(e) {
    function n(l) {
      return Yt(l, e);
    }
    if (0 < Vr.length) {
      Yt(Vr[0], e);
      for (var t = 1; t < Vr.length; t++) {
        var r = Vr[t];
        r.blockedOn === e && (r.blockedOn = null);
      }
    }
    for (In !== null && Yt(In, e), Wn !== null && Yt(Wn, e), Dn !== null && Yt(Dn, e), Kt.forEach(n), Qt.forEach(n), t = 0; t < Vn.length; t++) r = Vn[t], r.blockedOn === e && (r.blockedOn = null);
    for (; 0 < Vn.length && (t = Vn[0], t.blockedOn === null); ) Es(t), t.blockedOn === null && Vn.shift();
  }
  var gt = de.ReactCurrentBatchConfig, Hr = !0;
  function Oc(e, n, t, r) {
    var l = te, i = gt.transition;
    gt.transition = null;
    try {
      te = 1, ui(e, n, t, r);
    } finally {
      te = l, gt.transition = i;
    }
  }
  function Fc(e, n, t, r) {
    var l = te, i = gt.transition;
    gt.transition = null;
    try {
      te = 4, ui(e, n, t, r);
    } finally {
      te = l, gt.transition = i;
    }
  }
  function ui(e, n, t, r) {
    if (Hr) {
      var l = ai(e, n, t, r);
      if (l === null) zi(e, n, r, qr, t), js(e, r);
      else if (Tc(l, e, n, t, r)) r.stopPropagation();
      else if (js(e, r), n & 4 && -1 < Pc.indexOf(e)) {
        for (; l !== null; ) {
          var i = ar(l);
          if (i !== null && xs(i), i = ai(e, n, t, r), i === null && zi(e, n, r, qr, t), i === l) break;
          l = i;
        }
        l !== null && r.stopPropagation();
      } else zi(e, n, r, null, t);
    }
  }
  var qr = null;
  function ai(e, n, t, r) {
    if (qr = null, e = _l(r), e = nt(e), e !== null) if (n = et(e), n === null) e = null;
    else if (t = n.tag, t === 13) {
      if (e = as(n), e !== null) return e;
      e = null;
    } else if (t === 3) {
      if (n.stateNode.current.memoizedState.isDehydrated) return n.tag === 3 ? n.stateNode.containerInfo : null;
      e = null;
    } else n !== e && (e = null);
    return qr = e, null;
  }
  function zs(e) {
    switch (e) {
      case "cancel":
      case "click":
      case "close":
      case "contextmenu":
      case "copy":
      case "cut":
      case "auxclick":
      case "dblclick":
      case "dragend":
      case "dragstart":
      case "drop":
      case "focusin":
      case "focusout":
      case "input":
      case "invalid":
      case "keydown":
      case "keypress":
      case "keyup":
      case "mousedown":
      case "mouseup":
      case "paste":
      case "pause":
      case "play":
      case "pointercancel":
      case "pointerdown":
      case "pointerup":
      case "ratechange":
      case "reset":
      case "resize":
      case "seeked":
      case "submit":
      case "touchcancel":
      case "touchend":
      case "touchstart":
      case "volumechange":
      case "change":
      case "selectionchange":
      case "textInput":
      case "compositionstart":
      case "compositionend":
      case "compositionupdate":
      case "beforeblur":
      case "afterblur":
      case "beforeinput":
      case "blur":
      case "fullscreenchange":
      case "focus":
      case "hashchange":
      case "popstate":
      case "select":
      case "selectstart":
        return 1;
      case "drag":
      case "dragenter":
      case "dragexit":
      case "dragleave":
      case "dragover":
      case "mousemove":
      case "mouseout":
      case "mouseover":
      case "pointermove":
      case "pointerout":
      case "pointerover":
      case "scroll":
      case "toggle":
      case "touchmove":
      case "wheel":
      case "mouseenter":
      case "mouseleave":
      case "pointerenter":
      case "pointerleave":
        return 4;
      case "message":
        switch (wc()) {
          case ti:
            return 1;
          case ms:
            return 4;
          case Fr:
          case kc:
            return 16;
          case vs:
            return 536870912;
          default:
            return 16;
        }
      default:
        return 16;
    }
  }
  var Un = null, ci = null, Ar = null;
  function Cs() {
    if (Ar) return Ar;
    var e, n = ci, t = n.length, r, l = "value" in Un ? Un.value : Un.textContent, i = l.length;
    for (e = 0; e < t && n[e] === l[e]; e++) ;
    var o = t - e;
    for (r = 1; r <= o && n[t - r] === l[i - r]; r++) ;
    return Ar = l.slice(e, 1 < r ? 1 - r : void 0);
  }
  function Br(e) {
    var n = e.keyCode;
    return "charCode" in e ? (e = e.charCode, e === 0 && n === 13 && (e = 13)) : e = n, e === 10 && (e = 13), 32 <= e || e === 13 ? e : 0;
  }
  function Xr() {
    return !0;
  }
  function Rs() {
    return !1;
  }
  function nn(e) {
    function n(t, r, l, i, o) {
      this._reactName = t, this._targetInst = l, this.type = r, this.nativeEvent = i, this.target = o, this.currentTarget = null;
      for (var d in e) e.hasOwnProperty(d) && (t = e[d], this[d] = t ? t(i) : i[d]);
      return this.isDefaultPrevented = (i.defaultPrevented != null ? i.defaultPrevented : i.returnValue === !1) ? Xr : Rs, this.isPropagationStopped = Rs, this;
    }
    return P(n.prototype, { preventDefault: function() {
      this.defaultPrevented = !0;
      var t = this.nativeEvent;
      t && (t.preventDefault ? t.preventDefault() : typeof t.returnValue != "unknown" && (t.returnValue = !1), this.isDefaultPrevented = Xr);
    }, stopPropagation: function() {
      var t = this.nativeEvent;
      t && (t.stopPropagation ? t.stopPropagation() : typeof t.cancelBubble != "unknown" && (t.cancelBubble = !0), this.isPropagationStopped = Xr);
    }, persist: function() {
    }, isPersistent: Xr }), n;
  }
  var yt = { eventPhase: 0, bubbles: 0, cancelable: 0, timeStamp: function(e) {
    return e.timeStamp || Date.now();
  }, defaultPrevented: 0, isTrusted: 0 }, di = nn(yt), bt = P({}, yt, { view: 0, detail: 0 }), Mc = nn(bt), fi, pi, $t, Zr = P({}, bt, { screenX: 0, screenY: 0, clientX: 0, clientY: 0, pageX: 0, pageY: 0, ctrlKey: 0, shiftKey: 0, altKey: 0, metaKey: 0, getModifierState: mi, button: 0, buttons: 0, relatedTarget: function(e) {
    return e.relatedTarget === void 0 ? e.fromElement === e.srcElement ? e.toElement : e.fromElement : e.relatedTarget;
  }, movementX: function(e) {
    return "movementX" in e ? e.movementX : (e !== $t && ($t && e.type === "mousemove" ? (fi = e.screenX - $t.screenX, pi = e.screenY - $t.screenY) : pi = fi = 0, $t = e), fi);
  }, movementY: function(e) {
    return "movementY" in e ? e.movementY : pi;
  } }), Ps = nn(Zr), Ic = P({}, Zr, { dataTransfer: 0 }), Wc = nn(Ic), Dc = P({}, bt, { relatedTarget: 0 }), hi = nn(Dc), Vc = P({}, yt, { animationName: 0, elapsedTime: 0, pseudoElement: 0 }), Uc = nn(Vc), Hc = P({}, yt, { clipboardData: function(e) {
    return "clipboardData" in e ? e.clipboardData : window.clipboardData;
  } }), qc = nn(Hc), Ac = P({}, yt, { data: 0 }), Ts = nn(Ac), Bc = {
    Esc: "Escape",
    Spacebar: " ",
    Left: "ArrowLeft",
    Up: "ArrowUp",
    Right: "ArrowRight",
    Down: "ArrowDown",
    Del: "Delete",
    Win: "OS",
    Menu: "ContextMenu",
    Apps: "ContextMenu",
    Scroll: "ScrollLock",
    MozPrintableKey: "Unidentified"
  }, Xc = {
    8: "Backspace",
    9: "Tab",
    12: "Clear",
    13: "Enter",
    16: "Shift",
    17: "Control",
    18: "Alt",
    19: "Pause",
    20: "CapsLock",
    27: "Escape",
    32: " ",
    33: "PageUp",
    34: "PageDown",
    35: "End",
    36: "Home",
    37: "ArrowLeft",
    38: "ArrowUp",
    39: "ArrowRight",
    40: "ArrowDown",
    45: "Insert",
    46: "Delete",
    112: "F1",
    113: "F2",
    114: "F3",
    115: "F4",
    116: "F5",
    117: "F6",
    118: "F7",
    119: "F8",
    120: "F9",
    121: "F10",
    122: "F11",
    123: "F12",
    144: "NumLock",
    145: "ScrollLock",
    224: "Meta"
  }, Zc = { Alt: "altKey", Control: "ctrlKey", Meta: "metaKey", Shift: "shiftKey" };
  function Jc(e) {
    var n = this.nativeEvent;
    return n.getModifierState ? n.getModifierState(e) : (e = Zc[e]) ? !!n[e] : !1;
  }
  function mi() {
    return Jc;
  }
  var Kc = P({}, bt, { key: function(e) {
    if (e.key) {
      var n = Bc[e.key] || e.key;
      if (n !== "Unidentified") return n;
    }
    return e.type === "keypress" ? (e = Br(e), e === 13 ? "Enter" : String.fromCharCode(e)) : e.type === "keydown" || e.type === "keyup" ? Xc[e.keyCode] || "Unidentified" : "";
  }, code: 0, location: 0, ctrlKey: 0, shiftKey: 0, altKey: 0, metaKey: 0, repeat: 0, locale: 0, getModifierState: mi, charCode: function(e) {
    return e.type === "keypress" ? Br(e) : 0;
  }, keyCode: function(e) {
    return e.type === "keydown" || e.type === "keyup" ? e.keyCode : 0;
  }, which: function(e) {
    return e.type === "keypress" ? Br(e) : e.type === "keydown" || e.type === "keyup" ? e.keyCode : 0;
  } }), Qc = nn(Kc), Gc = P({}, Zr, { pointerId: 0, width: 0, height: 0, pressure: 0, tangentialPressure: 0, tiltX: 0, tiltY: 0, twist: 0, pointerType: 0, isPrimary: 0 }), Ls = nn(Gc), Yc = P({}, bt, { touches: 0, targetTouches: 0, changedTouches: 0, altKey: 0, metaKey: 0, ctrlKey: 0, shiftKey: 0, getModifierState: mi }), _c = nn(Yc), bc = P({}, yt, { propertyName: 0, elapsedTime: 0, pseudoElement: 0 }), $c = nn(bc), ed = P({}, Zr, {
    deltaX: function(e) {
      return "deltaX" in e ? e.deltaX : "wheelDeltaX" in e ? -e.wheelDeltaX : 0;
    },
    deltaY: function(e) {
      return "deltaY" in e ? e.deltaY : "wheelDeltaY" in e ? -e.wheelDeltaY : "wheelDelta" in e ? -e.wheelDelta : 0;
    },
    deltaZ: 0,
    deltaMode: 0
  }), nd = nn(ed), td = [9, 13, 27, 32], vi = T && "CompositionEvent" in window, er = null;
  T && "documentMode" in document && (er = document.documentMode);
  var rd = T && "TextEvent" in window && !er, Os = T && (!vi || er && 8 < er && 11 >= er), Fs = " ", Ms = !1;
  function Is(e, n) {
    switch (e) {
      case "keyup":
        return td.indexOf(n.keyCode) !== -1;
      case "keydown":
        return n.keyCode !== 229;
      case "keypress":
      case "mousedown":
      case "focusout":
        return !0;
      default:
        return !1;
    }
  }
  function Ws(e) {
    return e = e.detail, typeof e == "object" && "data" in e ? e.data : null;
  }
  var xt = !1;
  function ld(e, n) {
    switch (e) {
      case "compositionend":
        return Ws(n);
      case "keypress":
        return n.which !== 32 ? null : (Ms = !0, Fs);
      case "textInput":
        return e = n.data, e === Fs && Ms ? null : e;
      default:
        return null;
    }
  }
  function id(e, n) {
    if (xt) return e === "compositionend" || !vi && Is(e, n) ? (e = Cs(), Ar = ci = Un = null, xt = !1, e) : null;
    switch (e) {
      case "paste":
        return null;
      case "keypress":
        if (!(n.ctrlKey || n.altKey || n.metaKey) || n.ctrlKey && n.altKey) {
          if (n.char && 1 < n.char.length) return n.char;
          if (n.which) return String.fromCharCode(n.which);
        }
        return null;
      case "compositionend":
        return Os && n.locale !== "ko" ? null : n.data;
      default:
        return null;
    }
  }
  var od = { color: !0, date: !0, datetime: !0, "datetime-local": !0, email: !0, month: !0, number: !0, password: !0, range: !0, search: !0, tel: !0, text: !0, time: !0, url: !0, week: !0 };
  function Ds(e) {
    var n = e && e.nodeName && e.nodeName.toLowerCase();
    return n === "input" ? !!od[e.type] : n === "textarea";
  }
  function Vs(e, n, t, r) {
    ls(r), n = Yr(n, "onChange"), 0 < n.length && (t = new di("onChange", "change", null, t, r), e.push({ event: t, listeners: n }));
  }
  var nr = null, tr = null;
  function sd(e) {
    tu(e, 0);
  }
  function Jr(e) {
    var n = Et(e);
    if (Jo(n)) return e;
  }
  function ud(e, n) {
    if (e === "change") return n;
  }
  var Us = !1;
  if (T) {
    var gi;
    if (T) {
      var yi = "oninput" in document;
      if (!yi) {
        var Hs = document.createElement("div");
        Hs.setAttribute("oninput", "return;"), yi = typeof Hs.oninput == "function";
      }
      gi = yi;
    } else gi = !1;
    Us = gi && (!document.documentMode || 9 < document.documentMode);
  }
  function qs() {
    nr && (nr.detachEvent("onpropertychange", As), tr = nr = null);
  }
  function As(e) {
    if (e.propertyName === "value" && Jr(tr)) {
      var n = [];
      Vs(n, tr, e, _l(e)), us(sd, n);
    }
  }
  function ad(e, n, t) {
    e === "focusin" ? (qs(), nr = n, tr = t, nr.attachEvent("onpropertychange", As)) : e === "focusout" && qs();
  }
  function cd(e) {
    if (e === "selectionchange" || e === "keyup" || e === "keydown") return Jr(tr);
  }
  function dd(e, n) {
    if (e === "click") return Jr(n);
  }
  function fd(e, n) {
    if (e === "input" || e === "change") return Jr(n);
  }
  function pd(e, n) {
    return e === n && (e !== 0 || 1 / e === 1 / n) || e !== e && n !== n;
  }
  var hn = typeof Object.is == "function" ? Object.is : pd;
  function rr(e, n) {
    if (hn(e, n)) return !0;
    if (typeof e != "object" || e === null || typeof n != "object" || n === null) return !1;
    var t = Object.keys(e), r = Object.keys(n);
    if (t.length !== r.length) return !1;
    for (r = 0; r < t.length; r++) {
      var l = t[r];
      if (!R.call(n, l) || !hn(e[l], n[l])) return !1;
    }
    return !0;
  }
  function Bs(e) {
    for (; e && e.firstChild; ) e = e.firstChild;
    return e;
  }
  function Xs(e, n) {
    var t = Bs(e);
    e = 0;
    for (var r; t; ) {
      if (t.nodeType === 3) {
        if (r = e + t.textContent.length, e <= n && r >= n) return { node: t, offset: n - e };
        e = r;
      }
      e: {
        for (; t; ) {
          if (t.nextSibling) {
            t = t.nextSibling;
            break e;
          }
          t = t.parentNode;
        }
        t = void 0;
      }
      t = Bs(t);
    }
  }
  function Zs(e, n) {
    return e && n ? e === n ? !0 : e && e.nodeType === 3 ? !1 : n && n.nodeType === 3 ? Zs(e, n.parentNode) : "contains" in e ? e.contains(n) : e.compareDocumentPosition ? !!(e.compareDocumentPosition(n) & 16) : !1 : !1;
  }
  function Js() {
    for (var e = window, n = Pr(); n instanceof e.HTMLIFrameElement; ) {
      try {
        var t = typeof n.contentWindow.location.href == "string";
      } catch {
        t = !1;
      }
      if (t) e = n.contentWindow;
      else break;
      n = Pr(e.document);
    }
    return n;
  }
  function xi(e) {
    var n = e && e.nodeName && e.nodeName.toLowerCase();
    return n && (n === "input" && (e.type === "text" || e.type === "search" || e.type === "tel" || e.type === "url" || e.type === "password") || n === "textarea" || e.contentEditable === "true");
  }
  function hd(e) {
    var n = Js(), t = e.focusedElem, r = e.selectionRange;
    if (n !== t && t && t.ownerDocument && Zs(t.ownerDocument.documentElement, t)) {
      if (r !== null && xi(t)) {
        if (n = r.start, e = r.end, e === void 0 && (e = n), "selectionStart" in t) t.selectionStart = n, t.selectionEnd = Math.min(e, t.value.length);
        else if (e = (n = t.ownerDocument || document) && n.defaultView || window, e.getSelection) {
          e = e.getSelection();
          var l = t.textContent.length, i = Math.min(r.start, l);
          r = r.end === void 0 ? i : Math.min(r.end, l), !e.extend && i > r && (l = r, r = i, i = l), l = Xs(t, i);
          var o = Xs(
            t,
            r
          );
          l && o && (e.rangeCount !== 1 || e.anchorNode !== l.node || e.anchorOffset !== l.offset || e.focusNode !== o.node || e.focusOffset !== o.offset) && (n = n.createRange(), n.setStart(l.node, l.offset), e.removeAllRanges(), i > r ? (e.addRange(n), e.extend(o.node, o.offset)) : (n.setEnd(o.node, o.offset), e.addRange(n)));
        }
      }
      for (n = [], e = t; e = e.parentNode; ) e.nodeType === 1 && n.push({ element: e, left: e.scrollLeft, top: e.scrollTop });
      for (typeof t.focus == "function" && t.focus(), t = 0; t < n.length; t++) e = n[t], e.element.scrollLeft = e.left, e.element.scrollTop = e.top;
    }
  }
  var md = T && "documentMode" in document && 11 >= document.documentMode, wt = null, wi = null, lr = null, ki = !1;
  function Ks(e, n, t) {
    var r = t.window === t ? t.document : t.nodeType === 9 ? t : t.ownerDocument;
    ki || wt == null || wt !== Pr(r) || (r = wt, "selectionStart" in r && xi(r) ? r = { start: r.selectionStart, end: r.selectionEnd } : (r = (r.ownerDocument && r.ownerDocument.defaultView || window).getSelection(), r = { anchorNode: r.anchorNode, anchorOffset: r.anchorOffset, focusNode: r.focusNode, focusOffset: r.focusOffset }), lr && rr(lr, r) || (lr = r, r = Yr(wi, "onSelect"), 0 < r.length && (n = new di("onSelect", "select", null, n, t), e.push({ event: n, listeners: r }), n.target = wt)));
  }
  function Kr(e, n) {
    var t = {};
    return t[e.toLowerCase()] = n.toLowerCase(), t["Webkit" + e] = "webkit" + n, t["Moz" + e] = "moz" + n, t;
  }
  var kt = { animationend: Kr("Animation", "AnimationEnd"), animationiteration: Kr("Animation", "AnimationIteration"), animationstart: Kr("Animation", "AnimationStart"), transitionend: Kr("Transition", "TransitionEnd") }, Si = {}, Qs = {};
  T && (Qs = document.createElement("div").style, "AnimationEvent" in window || (delete kt.animationend.animation, delete kt.animationiteration.animation, delete kt.animationstart.animation), "TransitionEvent" in window || delete kt.transitionend.transition);
  function Qr(e) {
    if (Si[e]) return Si[e];
    if (!kt[e]) return e;
    var n = kt[e], t;
    for (t in n) if (n.hasOwnProperty(t) && t in Qs) return Si[e] = n[t];
    return e;
  }
  var Gs = Qr("animationend"), Ys = Qr("animationiteration"), _s = Qr("animationstart"), bs = Qr("transitionend"), $s = /* @__PURE__ */ new Map(), eu = "abort auxClick cancel canPlay canPlayThrough click close contextMenu copy cut drag dragEnd dragEnter dragExit dragLeave dragOver dragStart drop durationChange emptied encrypted ended error gotPointerCapture input invalid keyDown keyPress keyUp load loadedData loadedMetadata loadStart lostPointerCapture mouseDown mouseMove mouseOut mouseOver mouseUp paste pause play playing pointerCancel pointerDown pointerMove pointerOut pointerOver pointerUp progress rateChange reset resize seeked seeking stalled submit suspend timeUpdate touchCancel touchEnd touchStart volumeChange scroll toggle touchMove waiting wheel".split(" ");
  function Hn(e, n) {
    $s.set(e, n), E(n, [e]);
  }
  for (var ji = 0; ji < eu.length; ji++) {
    var Ei = eu[ji], vd = Ei.toLowerCase(), gd = Ei[0].toUpperCase() + Ei.slice(1);
    Hn(vd, "on" + gd);
  }
  Hn(Gs, "onAnimationEnd"), Hn(Ys, "onAnimationIteration"), Hn(_s, "onAnimationStart"), Hn("dblclick", "onDoubleClick"), Hn("focusin", "onFocus"), Hn("focusout", "onBlur"), Hn(bs, "onTransitionEnd"), L("onMouseEnter", ["mouseout", "mouseover"]), L("onMouseLeave", ["mouseout", "mouseover"]), L("onPointerEnter", ["pointerout", "pointerover"]), L("onPointerLeave", ["pointerout", "pointerover"]), E("onChange", "change click focusin focusout input keydown keyup selectionchange".split(" ")), E("onSelect", "focusout contextmenu dragend focusin keydown keyup mousedown mouseup selectionchange".split(" ")), E("onBeforeInput", ["compositionend", "keypress", "textInput", "paste"]), E("onCompositionEnd", "compositionend focusout keydown keypress keyup mousedown".split(" ")), E("onCompositionStart", "compositionstart focusout keydown keypress keyup mousedown".split(" ")), E("onCompositionUpdate", "compositionupdate focusout keydown keypress keyup mousedown".split(" "));
  var ir = "abort canplay canplaythrough durationchange emptied encrypted ended error loadeddata loadedmetadata loadstart pause play playing progress ratechange resize seeked seeking stalled suspend timeupdate volumechange waiting".split(" "), yd = new Set("cancel close invalid load scroll toggle".split(" ").concat(ir));
  function nu(e, n, t) {
    var r = e.type || "unknown-event";
    e.currentTarget = t, vc(r, n, void 0, e), e.currentTarget = null;
  }
  function tu(e, n) {
    n = (n & 4) !== 0;
    for (var t = 0; t < e.length; t++) {
      var r = e[t], l = r.event;
      r = r.listeners;
      e: {
        var i = void 0;
        if (n) for (var o = r.length - 1; 0 <= o; o--) {
          var d = r[o], f = d.instance, g = d.currentTarget;
          if (d = d.listener, f !== i && l.isPropagationStopped()) break e;
          nu(l, d, g), i = f;
        }
        else for (o = 0; o < r.length; o++) {
          if (d = r[o], f = d.instance, g = d.currentTarget, d = d.listener, f !== i && l.isPropagationStopped()) break e;
          nu(l, d, g), i = f;
        }
      }
    }
    if (Or) throw e = ni, Or = !1, ni = null, e;
  }
  function ue(e, n) {
    var t = n[Oi];
    t === void 0 && (t = n[Oi] = /* @__PURE__ */ new Set());
    var r = e + "__bubble";
    t.has(r) || (ru(n, e, 2, !1), t.add(r));
  }
  function Ni(e, n, t) {
    var r = 0;
    n && (r |= 4), ru(t, e, r, n);
  }
  var Gr = "_reactListening" + Math.random().toString(36).slice(2);
  function or(e) {
    if (!e[Gr]) {
      e[Gr] = !0, y.forEach(function(t) {
        t !== "selectionchange" && (yd.has(t) || Ni(t, !1, e), Ni(t, !0, e));
      });
      var n = e.nodeType === 9 ? e : e.ownerDocument;
      n === null || n[Gr] || (n[Gr] = !0, Ni("selectionchange", !1, n));
    }
  }
  function ru(e, n, t, r) {
    switch (zs(n)) {
      case 1:
        var l = Oc;
        break;
      case 4:
        l = Fc;
        break;
      default:
        l = ui;
    }
    t = l.bind(null, n, t, e), l = void 0, !ei || n !== "touchstart" && n !== "touchmove" && n !== "wheel" || (l = !0), r ? l !== void 0 ? e.addEventListener(n, t, { capture: !0, passive: l }) : e.addEventListener(n, t, !0) : l !== void 0 ? e.addEventListener(n, t, { passive: l }) : e.addEventListener(n, t, !1);
  }
  function zi(e, n, t, r, l) {
    var i = r;
    if ((n & 1) === 0 && (n & 2) === 0 && r !== null) e: for (; ; ) {
      if (r === null) return;
      var o = r.tag;
      if (o === 3 || o === 4) {
        var d = r.stateNode.containerInfo;
        if (d === l || d.nodeType === 8 && d.parentNode === l) break;
        if (o === 4) for (o = r.return; o !== null; ) {
          var f = o.tag;
          if ((f === 3 || f === 4) && (f = o.stateNode.containerInfo, f === l || f.nodeType === 8 && f.parentNode === l)) return;
          o = o.return;
        }
        for (; d !== null; ) {
          if (o = nt(d), o === null) return;
          if (f = o.tag, f === 5 || f === 6) {
            r = i = o;
            continue e;
          }
          d = d.parentNode;
        }
      }
      r = r.return;
    }
    us(function() {
      var g = i, N = _l(t), z = [];
      e: {
        var j = $s.get(e);
        if (j !== void 0) {
          var O = di, I = e;
          switch (e) {
            case "keypress":
              if (Br(t) === 0) break e;
            case "keydown":
            case "keyup":
              O = Qc;
              break;
            case "focusin":
              I = "focus", O = hi;
              break;
            case "focusout":
              I = "blur", O = hi;
              break;
            case "beforeblur":
            case "afterblur":
              O = hi;
              break;
            case "click":
              if (t.button === 2) break e;
            case "auxclick":
            case "dblclick":
            case "mousedown":
            case "mousemove":
            case "mouseup":
            case "mouseout":
            case "mouseover":
            case "contextmenu":
              O = Ps;
              break;
            case "drag":
            case "dragend":
            case "dragenter":
            case "dragexit":
            case "dragleave":
            case "dragover":
            case "dragstart":
            case "drop":
              O = Wc;
              break;
            case "touchcancel":
            case "touchend":
            case "touchmove":
            case "touchstart":
              O = _c;
              break;
            case Gs:
            case Ys:
            case _s:
              O = Uc;
              break;
            case bs:
              O = $c;
              break;
            case "scroll":
              O = Mc;
              break;
            case "wheel":
              O = nd;
              break;
            case "copy":
            case "cut":
            case "paste":
              O = qc;
              break;
            case "gotpointercapture":
            case "lostpointercapture":
            case "pointercancel":
            case "pointerdown":
            case "pointermove":
            case "pointerout":
            case "pointerover":
            case "pointerup":
              O = Ls;
          }
          var W = (n & 4) !== 0, ke = !W && e === "scroll", m = W ? j !== null ? j + "Capture" : null : j;
          W = [];
          for (var p = g, v; p !== null; ) {
            v = p;
            var C = v.stateNode;
            if (v.tag === 5 && C !== null && (v = C, m !== null && (C = At(p, m), C != null && W.push(sr(p, C, v)))), ke) break;
            p = p.return;
          }
          0 < W.length && (j = new O(j, I, null, t, N), z.push({ event: j, listeners: W }));
        }
      }
      if ((n & 7) === 0) {
        e: {
          if (j = e === "mouseover" || e === "pointerover", O = e === "mouseout" || e === "pointerout", j && t !== Yl && (I = t.relatedTarget || t.fromElement) && (nt(I) || I[Cn])) break e;
          if ((O || j) && (j = N.window === N ? N : (j = N.ownerDocument) ? j.defaultView || j.parentWindow : window, O ? (I = t.relatedTarget || t.toElement, O = g, I = I ? nt(I) : null, I !== null && (ke = et(I), I !== ke || I.tag !== 5 && I.tag !== 6) && (I = null)) : (O = null, I = g), O !== I)) {
            if (W = Ps, C = "onMouseLeave", m = "onMouseEnter", p = "mouse", (e === "pointerout" || e === "pointerover") && (W = Ls, C = "onPointerLeave", m = "onPointerEnter", p = "pointer"), ke = O == null ? j : Et(O), v = I == null ? j : Et(I), j = new W(C, p + "leave", O, t, N), j.target = ke, j.relatedTarget = v, C = null, nt(N) === g && (W = new W(m, p + "enter", I, t, N), W.target = v, W.relatedTarget = ke, C = W), ke = C, O && I) n: {
              for (W = O, m = I, p = 0, v = W; v; v = St(v)) p++;
              for (v = 0, C = m; C; C = St(C)) v++;
              for (; 0 < p - v; ) W = St(W), p--;
              for (; 0 < v - p; ) m = St(m), v--;
              for (; p--; ) {
                if (W === m || m !== null && W === m.alternate) break n;
                W = St(W), m = St(m);
              }
              W = null;
            }
            else W = null;
            O !== null && lu(z, j, O, W, !1), I !== null && ke !== null && lu(z, ke, I, W, !0);
          }
        }
        e: {
          if (j = g ? Et(g) : window, O = j.nodeName && j.nodeName.toLowerCase(), O === "select" || O === "input" && j.type === "file") var D = ud;
          else if (Ds(j)) if (Us) D = fd;
          else {
            D = cd;
            var U = ad;
          }
          else (O = j.nodeName) && O.toLowerCase() === "input" && (j.type === "checkbox" || j.type === "radio") && (D = dd);
          if (D && (D = D(e, g))) {
            Vs(z, D, t, N);
            break e;
          }
          U && U(e, j, g), e === "focusout" && (U = j._wrapperState) && U.controlled && j.type === "number" && Zl(j, "number", j.value);
        }
        switch (U = g ? Et(g) : window, e) {
          case "focusin":
            (Ds(U) || U.contentEditable === "true") && (wt = U, wi = g, lr = null);
            break;
          case "focusout":
            lr = wi = wt = null;
            break;
          case "mousedown":
            ki = !0;
            break;
          case "contextmenu":
          case "mouseup":
          case "dragend":
            ki = !1, Ks(z, t, N);
            break;
          case "selectionchange":
            if (md) break;
          case "keydown":
          case "keyup":
            Ks(z, t, N);
        }
        var H;
        if (vi) e: {
          switch (e) {
            case "compositionstart":
              var q = "onCompositionStart";
              break e;
            case "compositionend":
              q = "onCompositionEnd";
              break e;
            case "compositionupdate":
              q = "onCompositionUpdate";
              break e;
          }
          q = void 0;
        }
        else xt ? Is(e, t) && (q = "onCompositionEnd") : e === "keydown" && t.keyCode === 229 && (q = "onCompositionStart");
        q && (Os && t.locale !== "ko" && (xt || q !== "onCompositionStart" ? q === "onCompositionEnd" && xt && (H = Cs()) : (Un = N, ci = "value" in Un ? Un.value : Un.textContent, xt = !0)), U = Yr(g, q), 0 < U.length && (q = new Ts(q, e, null, t, N), z.push({ event: q, listeners: U }), H ? q.data = H : (H = Ws(t), H !== null && (q.data = H)))), (H = rd ? ld(e, t) : id(e, t)) && (g = Yr(g, "onBeforeInput"), 0 < g.length && (N = new Ts("onBeforeInput", "beforeinput", null, t, N), z.push({ event: N, listeners: g }), N.data = H));
      }
      tu(z, n);
    });
  }
  function sr(e, n, t) {
    return { instance: e, listener: n, currentTarget: t };
  }
  function Yr(e, n) {
    for (var t = n + "Capture", r = []; e !== null; ) {
      var l = e, i = l.stateNode;
      l.tag === 5 && i !== null && (l = i, i = At(e, t), i != null && r.unshift(sr(e, i, l)), i = At(e, n), i != null && r.push(sr(e, i, l))), e = e.return;
    }
    return r;
  }
  function St(e) {
    if (e === null) return null;
    do
      e = e.return;
    while (e && e.tag !== 5);
    return e || null;
  }
  function lu(e, n, t, r, l) {
    for (var i = n._reactName, o = []; t !== null && t !== r; ) {
      var d = t, f = d.alternate, g = d.stateNode;
      if (f !== null && f === r) break;
      d.tag === 5 && g !== null && (d = g, l ? (f = At(t, i), f != null && o.unshift(sr(t, f, d))) : l || (f = At(t, i), f != null && o.push(sr(t, f, d)))), t = t.return;
    }
    o.length !== 0 && e.push({ event: n, listeners: o });
  }
  var xd = /\r\n?/g, wd = /\u0000|\uFFFD/g;
  function iu(e) {
    return (typeof e == "string" ? e : "" + e).replace(xd, `
`).replace(wd, "");
  }
  function _r(e, n, t) {
    if (n = iu(n), iu(e) !== n && t) throw Error(c(425));
  }
  function br() {
  }
  var Ci = null, Ri = null;
  function Pi(e, n) {
    return e === "textarea" || e === "noscript" || typeof n.children == "string" || typeof n.children == "number" || typeof n.dangerouslySetInnerHTML == "object" && n.dangerouslySetInnerHTML !== null && n.dangerouslySetInnerHTML.__html != null;
  }
  var Ti = typeof setTimeout == "function" ? setTimeout : void 0, kd = typeof clearTimeout == "function" ? clearTimeout : void 0, ou = typeof Promise == "function" ? Promise : void 0, Sd = typeof queueMicrotask == "function" ? queueMicrotask : typeof ou < "u" ? function(e) {
    return ou.resolve(null).then(e).catch(jd);
  } : Ti;
  function jd(e) {
    setTimeout(function() {
      throw e;
    });
  }
  function Li(e, n) {
    var t = n, r = 0;
    do {
      var l = t.nextSibling;
      if (e.removeChild(t), l && l.nodeType === 8) if (t = l.data, t === "/$") {
        if (r === 0) {
          e.removeChild(l), _t(n);
          return;
        }
        r--;
      } else t !== "$" && t !== "$?" && t !== "$!" || r++;
      t = l;
    } while (t);
    _t(n);
  }
  function qn(e) {
    for (; e != null; e = e.nextSibling) {
      var n = e.nodeType;
      if (n === 1 || n === 3) break;
      if (n === 8) {
        if (n = e.data, n === "$" || n === "$!" || n === "$?") break;
        if (n === "/$") return null;
      }
    }
    return e;
  }
  function su(e) {
    e = e.previousSibling;
    for (var n = 0; e; ) {
      if (e.nodeType === 8) {
        var t = e.data;
        if (t === "$" || t === "$!" || t === "$?") {
          if (n === 0) return e;
          n--;
        } else t === "/$" && n++;
      }
      e = e.previousSibling;
    }
    return null;
  }
  var jt = Math.random().toString(36).slice(2), jn = "__reactFiber$" + jt, ur = "__reactProps$" + jt, Cn = "__reactContainer$" + jt, Oi = "__reactEvents$" + jt, Ed = "__reactListeners$" + jt, Nd = "__reactHandles$" + jt;
  function nt(e) {
    var n = e[jn];
    if (n) return n;
    for (var t = e.parentNode; t; ) {
      if (n = t[Cn] || t[jn]) {
        if (t = n.alternate, n.child !== null || t !== null && t.child !== null) for (e = su(e); e !== null; ) {
          if (t = e[jn]) return t;
          e = su(e);
        }
        return n;
      }
      e = t, t = e.parentNode;
    }
    return null;
  }
  function ar(e) {
    return e = e[jn] || e[Cn], !e || e.tag !== 5 && e.tag !== 6 && e.tag !== 13 && e.tag !== 3 ? null : e;
  }
  function Et(e) {
    if (e.tag === 5 || e.tag === 6) return e.stateNode;
    throw Error(c(33));
  }
  function $r(e) {
    return e[ur] || null;
  }
  var Fi = [], Nt = -1;
  function An(e) {
    return { current: e };
  }
  function ae(e) {
    0 > Nt || (e.current = Fi[Nt], Fi[Nt] = null, Nt--);
  }
  function ie(e, n) {
    Nt++, Fi[Nt] = e.current, e.current = n;
  }
  var Bn = {}, Ve = An(Bn), Je = An(!1), tt = Bn;
  function zt(e, n) {
    var t = e.type.contextTypes;
    if (!t) return Bn;
    var r = e.stateNode;
    if (r && r.__reactInternalMemoizedUnmaskedChildContext === n) return r.__reactInternalMemoizedMaskedChildContext;
    var l = {}, i;
    for (i in t) l[i] = n[i];
    return r && (e = e.stateNode, e.__reactInternalMemoizedUnmaskedChildContext = n, e.__reactInternalMemoizedMaskedChildContext = l), l;
  }
  function Ke(e) {
    return e = e.childContextTypes, e != null;
  }
  function el() {
    ae(Je), ae(Ve);
  }
  function uu(e, n, t) {
    if (Ve.current !== Bn) throw Error(c(168));
    ie(Ve, n), ie(Je, t);
  }
  function au(e, n, t) {
    var r = e.stateNode;
    if (n = n.childContextTypes, typeof r.getChildContext != "function") return t;
    r = r.getChildContext();
    for (var l in r) if (!(l in n)) throw Error(c(108, le(e) || "Unknown", l));
    return P({}, t, r);
  }
  function nl(e) {
    return e = (e = e.stateNode) && e.__reactInternalMemoizedMergedChildContext || Bn, tt = Ve.current, ie(Ve, e), ie(Je, Je.current), !0;
  }
  function cu(e, n, t) {
    var r = e.stateNode;
    if (!r) throw Error(c(169));
    t ? (e = au(e, n, tt), r.__reactInternalMemoizedMergedChildContext = e, ae(Je), ae(Ve), ie(Ve, e)) : ae(Je), ie(Je, t);
  }
  var Rn = null, tl = !1, Mi = !1;
  function du(e) {
    Rn === null ? Rn = [e] : Rn.push(e);
  }
  function zd(e) {
    tl = !0, du(e);
  }
  function Xn() {
    if (!Mi && Rn !== null) {
      Mi = !0;
      var e = 0, n = te;
      try {
        var t = Rn;
        for (te = 1; e < t.length; e++) {
          var r = t[e];
          do
            r = r(!0);
          while (r !== null);
        }
        Rn = null, tl = !1;
      } catch (l) {
        throw Rn !== null && (Rn = Rn.slice(e + 1)), ps(ti, Xn), l;
      } finally {
        te = n, Mi = !1;
      }
    }
    return null;
  }
  var Ct = [], Rt = 0, rl = null, ll = 0, sn = [], un = 0, rt = null, Pn = 1, Tn = "";
  function lt(e, n) {
    Ct[Rt++] = ll, Ct[Rt++] = rl, rl = e, ll = n;
  }
  function fu(e, n, t) {
    sn[un++] = Pn, sn[un++] = Tn, sn[un++] = rt, rt = e;
    var r = Pn;
    e = Tn;
    var l = 32 - pn(r) - 1;
    r &= ~(1 << l), t += 1;
    var i = 32 - pn(n) + l;
    if (30 < i) {
      var o = l - l % 5;
      i = (r & (1 << o) - 1).toString(32), r >>= o, l -= o, Pn = 1 << 32 - pn(n) + l | t << l | r, Tn = i + e;
    } else Pn = 1 << i | t << l | r, Tn = e;
  }
  function Ii(e) {
    e.return !== null && (lt(e, 1), fu(e, 1, 0));
  }
  function Wi(e) {
    for (; e === rl; ) rl = Ct[--Rt], Ct[Rt] = null, ll = Ct[--Rt], Ct[Rt] = null;
    for (; e === rt; ) rt = sn[--un], sn[un] = null, Tn = sn[--un], sn[un] = null, Pn = sn[--un], sn[un] = null;
  }
  var tn = null, rn = null, he = !1, mn = null;
  function pu(e, n) {
    var t = fn(5, null, null, 0);
    t.elementType = "DELETED", t.stateNode = n, t.return = e, n = e.deletions, n === null ? (e.deletions = [t], e.flags |= 16) : n.push(t);
  }
  function hu(e, n) {
    switch (e.tag) {
      case 5:
        var t = e.type;
        return n = n.nodeType !== 1 || t.toLowerCase() !== n.nodeName.toLowerCase() ? null : n, n !== null ? (e.stateNode = n, tn = e, rn = qn(n.firstChild), !0) : !1;
      case 6:
        return n = e.pendingProps === "" || n.nodeType !== 3 ? null : n, n !== null ? (e.stateNode = n, tn = e, rn = null, !0) : !1;
      case 13:
        return n = n.nodeType !== 8 ? null : n, n !== null ? (t = rt !== null ? { id: Pn, overflow: Tn } : null, e.memoizedState = { dehydrated: n, treeContext: t, retryLane: 1073741824 }, t = fn(18, null, null, 0), t.stateNode = n, t.return = e, e.child = t, tn = e, rn = null, !0) : !1;
      default:
        return !1;
    }
  }
  function Di(e) {
    return (e.mode & 1) !== 0 && (e.flags & 128) === 0;
  }
  function Vi(e) {
    if (he) {
      var n = rn;
      if (n) {
        var t = n;
        if (!hu(e, n)) {
          if (Di(e)) throw Error(c(418));
          n = qn(t.nextSibling);
          var r = tn;
          n && hu(e, n) ? pu(r, t) : (e.flags = e.flags & -4097 | 2, he = !1, tn = e);
        }
      } else {
        if (Di(e)) throw Error(c(418));
        e.flags = e.flags & -4097 | 2, he = !1, tn = e;
      }
    }
  }
  function mu(e) {
    for (e = e.return; e !== null && e.tag !== 5 && e.tag !== 3 && e.tag !== 13; ) e = e.return;
    tn = e;
  }
  function il(e) {
    if (e !== tn) return !1;
    if (!he) return mu(e), he = !0, !1;
    var n;
    if ((n = e.tag !== 3) && !(n = e.tag !== 5) && (n = e.type, n = n !== "head" && n !== "body" && !Pi(e.type, e.memoizedProps)), n && (n = rn)) {
      if (Di(e)) throw vu(), Error(c(418));
      for (; n; ) pu(e, n), n = qn(n.nextSibling);
    }
    if (mu(e), e.tag === 13) {
      if (e = e.memoizedState, e = e !== null ? e.dehydrated : null, !e) throw Error(c(317));
      e: {
        for (e = e.nextSibling, n = 0; e; ) {
          if (e.nodeType === 8) {
            var t = e.data;
            if (t === "/$") {
              if (n === 0) {
                rn = qn(e.nextSibling);
                break e;
              }
              n--;
            } else t !== "$" && t !== "$!" && t !== "$?" || n++;
          }
          e = e.nextSibling;
        }
        rn = null;
      }
    } else rn = tn ? qn(e.stateNode.nextSibling) : null;
    return !0;
  }
  function vu() {
    for (var e = rn; e; ) e = qn(e.nextSibling);
  }
  function Pt() {
    rn = tn = null, he = !1;
  }
  function Ui(e) {
    mn === null ? mn = [e] : mn.push(e);
  }
  var Cd = de.ReactCurrentBatchConfig;
  function cr(e, n, t) {
    if (e = t.ref, e !== null && typeof e != "function" && typeof e != "object") {
      if (t._owner) {
        if (t = t._owner, t) {
          if (t.tag !== 1) throw Error(c(309));
          var r = t.stateNode;
        }
        if (!r) throw Error(c(147, e));
        var l = r, i = "" + e;
        return n !== null && n.ref !== null && typeof n.ref == "function" && n.ref._stringRef === i ? n.ref : (n = function(o) {
          var d = l.refs;
          o === null ? delete d[i] : d[i] = o;
        }, n._stringRef = i, n);
      }
      if (typeof e != "string") throw Error(c(284));
      if (!t._owner) throw Error(c(290, e));
    }
    return e;
  }
  function ol(e, n) {
    throw e = Object.prototype.toString.call(n), Error(c(31, e === "[object Object]" ? "object with keys {" + Object.keys(n).join(", ") + "}" : e));
  }
  function gu(e) {
    var n = e._init;
    return n(e._payload);
  }
  function yu(e) {
    function n(m, p) {
      if (e) {
        var v = m.deletions;
        v === null ? (m.deletions = [p], m.flags |= 16) : v.push(p);
      }
    }
    function t(m, p) {
      if (!e) return null;
      for (; p !== null; ) n(m, p), p = p.sibling;
      return null;
    }
    function r(m, p) {
      for (m = /* @__PURE__ */ new Map(); p !== null; ) p.key !== null ? m.set(p.key, p) : m.set(p.index, p), p = p.sibling;
      return m;
    }
    function l(m, p) {
      return m = bn(m, p), m.index = 0, m.sibling = null, m;
    }
    function i(m, p, v) {
      return m.index = v, e ? (v = m.alternate, v !== null ? (v = v.index, v < p ? (m.flags |= 2, p) : v) : (m.flags |= 2, p)) : (m.flags |= 1048576, p);
    }
    function o(m) {
      return e && m.alternate === null && (m.flags |= 2), m;
    }
    function d(m, p, v, C) {
      return p === null || p.tag !== 6 ? (p = Lo(v, m.mode, C), p.return = m, p) : (p = l(p, v), p.return = m, p);
    }
    function f(m, p, v, C) {
      var D = v.type;
      return D === Se ? N(m, p, v.props.children, C, v.key) : p !== null && (p.elementType === D || typeof D == "object" && D !== null && D.$$typeof === Oe && gu(D) === p.type) ? (C = l(p, v.props), C.ref = cr(m, p, v), C.return = m, C) : (C = Tl(v.type, v.key, v.props, null, m.mode, C), C.ref = cr(m, p, v), C.return = m, C);
    }
    function g(m, p, v, C) {
      return p === null || p.tag !== 4 || p.stateNode.containerInfo !== v.containerInfo || p.stateNode.implementation !== v.implementation ? (p = Oo(v, m.mode, C), p.return = m, p) : (p = l(p, v.children || []), p.return = m, p);
    }
    function N(m, p, v, C, D) {
      return p === null || p.tag !== 7 ? (p = ft(v, m.mode, C, D), p.return = m, p) : (p = l(p, v), p.return = m, p);
    }
    function z(m, p, v) {
      if (typeof p == "string" && p !== "" || typeof p == "number") return p = Lo("" + p, m.mode, v), p.return = m, p;
      if (typeof p == "object" && p !== null) {
        switch (p.$$typeof) {
          case X:
            return v = Tl(p.type, p.key, p.props, null, m.mode, v), v.ref = cr(m, null, p), v.return = m, v;
          case fe:
            return p = Oo(p, m.mode, v), p.return = m, p;
          case Oe:
            var C = p._init;
            return z(m, C(p._payload), v);
        }
        if (Ut(p) || F(p)) return p = ft(p, m.mode, v, null), p.return = m, p;
        ol(m, p);
      }
      return null;
    }
    function j(m, p, v, C) {
      var D = p !== null ? p.key : null;
      if (typeof v == "string" && v !== "" || typeof v == "number") return D !== null ? null : d(m, p, "" + v, C);
      if (typeof v == "object" && v !== null) {
        switch (v.$$typeof) {
          case X:
            return v.key === D ? f(m, p, v, C) : null;
          case fe:
            return v.key === D ? g(m, p, v, C) : null;
          case Oe:
            return D = v._init, j(
              m,
              p,
              D(v._payload),
              C
            );
        }
        if (Ut(v) || F(v)) return D !== null ? null : N(m, p, v, C, null);
        ol(m, v);
      }
      return null;
    }
    function O(m, p, v, C, D) {
      if (typeof C == "string" && C !== "" || typeof C == "number") return m = m.get(v) || null, d(p, m, "" + C, D);
      if (typeof C == "object" && C !== null) {
        switch (C.$$typeof) {
          case X:
            return m = m.get(C.key === null ? v : C.key) || null, f(p, m, C, D);
          case fe:
            return m = m.get(C.key === null ? v : C.key) || null, g(p, m, C, D);
          case Oe:
            var U = C._init;
            return O(m, p, v, U(C._payload), D);
        }
        if (Ut(C) || F(C)) return m = m.get(v) || null, N(p, m, C, D, null);
        ol(p, C);
      }
      return null;
    }
    function I(m, p, v, C) {
      for (var D = null, U = null, H = p, q = p = 0, Le = null; H !== null && q < v.length; q++) {
        H.index > q ? (Le = H, H = null) : Le = H.sibling;
        var $ = j(m, H, v[q], C);
        if ($ === null) {
          H === null && (H = Le);
          break;
        }
        e && H && $.alternate === null && n(m, H), p = i($, p, q), U === null ? D = $ : U.sibling = $, U = $, H = Le;
      }
      if (q === v.length) return t(m, H), he && lt(m, q), D;
      if (H === null) {
        for (; q < v.length; q++) H = z(m, v[q], C), H !== null && (p = i(H, p, q), U === null ? D = H : U.sibling = H, U = H);
        return he && lt(m, q), D;
      }
      for (H = r(m, H); q < v.length; q++) Le = O(H, m, q, v[q], C), Le !== null && (e && Le.alternate !== null && H.delete(Le.key === null ? q : Le.key), p = i(Le, p, q), U === null ? D = Le : U.sibling = Le, U = Le);
      return e && H.forEach(function($n) {
        return n(m, $n);
      }), he && lt(m, q), D;
    }
    function W(m, p, v, C) {
      var D = F(v);
      if (typeof D != "function") throw Error(c(150));
      if (v = D.call(v), v == null) throw Error(c(151));
      for (var U = D = null, H = p, q = p = 0, Le = null, $ = v.next(); H !== null && !$.done; q++, $ = v.next()) {
        H.index > q ? (Le = H, H = null) : Le = H.sibling;
        var $n = j(m, H, $.value, C);
        if ($n === null) {
          H === null && (H = Le);
          break;
        }
        e && H && $n.alternate === null && n(m, H), p = i($n, p, q), U === null ? D = $n : U.sibling = $n, U = $n, H = Le;
      }
      if ($.done) return t(
        m,
        H
      ), he && lt(m, q), D;
      if (H === null) {
        for (; !$.done; q++, $ = v.next()) $ = z(m, $.value, C), $ !== null && (p = i($, p, q), U === null ? D = $ : U.sibling = $, U = $);
        return he && lt(m, q), D;
      }
      for (H = r(m, H); !$.done; q++, $ = v.next()) $ = O(H, m, q, $.value, C), $ !== null && (e && $.alternate !== null && H.delete($.key === null ? q : $.key), p = i($, p, q), U === null ? D = $ : U.sibling = $, U = $);
      return e && H.forEach(function(sf) {
        return n(m, sf);
      }), he && lt(m, q), D;
    }
    function ke(m, p, v, C) {
      if (typeof v == "object" && v !== null && v.type === Se && v.key === null && (v = v.props.children), typeof v == "object" && v !== null) {
        switch (v.$$typeof) {
          case X:
            e: {
              for (var D = v.key, U = p; U !== null; ) {
                if (U.key === D) {
                  if (D = v.type, D === Se) {
                    if (U.tag === 7) {
                      t(m, U.sibling), p = l(U, v.props.children), p.return = m, m = p;
                      break e;
                    }
                  } else if (U.elementType === D || typeof D == "object" && D !== null && D.$$typeof === Oe && gu(D) === U.type) {
                    t(m, U.sibling), p = l(U, v.props), p.ref = cr(m, U, v), p.return = m, m = p;
                    break e;
                  }
                  t(m, U);
                  break;
                } else n(m, U);
                U = U.sibling;
              }
              v.type === Se ? (p = ft(v.props.children, m.mode, C, v.key), p.return = m, m = p) : (C = Tl(v.type, v.key, v.props, null, m.mode, C), C.ref = cr(m, p, v), C.return = m, m = C);
            }
            return o(m);
          case fe:
            e: {
              for (U = v.key; p !== null; ) {
                if (p.key === U) if (p.tag === 4 && p.stateNode.containerInfo === v.containerInfo && p.stateNode.implementation === v.implementation) {
                  t(m, p.sibling), p = l(p, v.children || []), p.return = m, m = p;
                  break e;
                } else {
                  t(m, p);
                  break;
                }
                else n(m, p);
                p = p.sibling;
              }
              p = Oo(v, m.mode, C), p.return = m, m = p;
            }
            return o(m);
          case Oe:
            return U = v._init, ke(m, p, U(v._payload), C);
        }
        if (Ut(v)) return I(m, p, v, C);
        if (F(v)) return W(m, p, v, C);
        ol(m, v);
      }
      return typeof v == "string" && v !== "" || typeof v == "number" ? (v = "" + v, p !== null && p.tag === 6 ? (t(m, p.sibling), p = l(p, v), p.return = m, m = p) : (t(m, p), p = Lo(v, m.mode, C), p.return = m, m = p), o(m)) : t(m, p);
    }
    return ke;
  }
  var Tt = yu(!0), xu = yu(!1), sl = An(null), ul = null, Lt = null, Hi = null;
  function qi() {
    Hi = Lt = ul = null;
  }
  function Ai(e) {
    var n = sl.current;
    ae(sl), e._currentValue = n;
  }
  function Bi(e, n, t) {
    for (; e !== null; ) {
      var r = e.alternate;
      if ((e.childLanes & n) !== n ? (e.childLanes |= n, r !== null && (r.childLanes |= n)) : r !== null && (r.childLanes & n) !== n && (r.childLanes |= n), e === t) break;
      e = e.return;
    }
  }
  function Ot(e, n) {
    ul = e, Hi = Lt = null, e = e.dependencies, e !== null && e.firstContext !== null && ((e.lanes & n) !== 0 && (Qe = !0), e.firstContext = null);
  }
  function an(e) {
    var n = e._currentValue;
    if (Hi !== e) if (e = { context: e, memoizedValue: n, next: null }, Lt === null) {
      if (ul === null) throw Error(c(308));
      Lt = e, ul.dependencies = { lanes: 0, firstContext: e };
    } else Lt = Lt.next = e;
    return n;
  }
  var it = null;
  function Xi(e) {
    it === null ? it = [e] : it.push(e);
  }
  function wu(e, n, t, r) {
    var l = n.interleaved;
    return l === null ? (t.next = t, Xi(n)) : (t.next = l.next, l.next = t), n.interleaved = t, Ln(e, r);
  }
  function Ln(e, n) {
    e.lanes |= n;
    var t = e.alternate;
    for (t !== null && (t.lanes |= n), t = e, e = e.return; e !== null; ) e.childLanes |= n, t = e.alternate, t !== null && (t.childLanes |= n), t = e, e = e.return;
    return t.tag === 3 ? t.stateNode : null;
  }
  var Zn = !1;
  function Zi(e) {
    e.updateQueue = { baseState: e.memoizedState, firstBaseUpdate: null, lastBaseUpdate: null, shared: { pending: null, interleaved: null, lanes: 0 }, effects: null };
  }
  function ku(e, n) {
    e = e.updateQueue, n.updateQueue === e && (n.updateQueue = { baseState: e.baseState, firstBaseUpdate: e.firstBaseUpdate, lastBaseUpdate: e.lastBaseUpdate, shared: e.shared, effects: e.effects });
  }
  function On(e, n) {
    return { eventTime: e, lane: n, tag: 0, payload: null, callback: null, next: null };
  }
  function Jn(e, n, t) {
    var r = e.updateQueue;
    if (r === null) return null;
    if (r = r.shared, (Y & 2) !== 0) {
      var l = r.pending;
      return l === null ? n.next = n : (n.next = l.next, l.next = n), r.pending = n, Ln(e, t);
    }
    return l = r.interleaved, l === null ? (n.next = n, Xi(r)) : (n.next = l.next, l.next = n), r.interleaved = n, Ln(e, t);
  }
  function al(e, n, t) {
    if (n = n.updateQueue, n !== null && (n = n.shared, (t & 4194240) !== 0)) {
      var r = n.lanes;
      r &= e.pendingLanes, t |= r, n.lanes = t, ii(e, t);
    }
  }
  function Su(e, n) {
    var t = e.updateQueue, r = e.alternate;
    if (r !== null && (r = r.updateQueue, t === r)) {
      var l = null, i = null;
      if (t = t.firstBaseUpdate, t !== null) {
        do {
          var o = { eventTime: t.eventTime, lane: t.lane, tag: t.tag, payload: t.payload, callback: t.callback, next: null };
          i === null ? l = i = o : i = i.next = o, t = t.next;
        } while (t !== null);
        i === null ? l = i = n : i = i.next = n;
      } else l = i = n;
      t = { baseState: r.baseState, firstBaseUpdate: l, lastBaseUpdate: i, shared: r.shared, effects: r.effects }, e.updateQueue = t;
      return;
    }
    e = t.lastBaseUpdate, e === null ? t.firstBaseUpdate = n : e.next = n, t.lastBaseUpdate = n;
  }
  function cl(e, n, t, r) {
    var l = e.updateQueue;
    Zn = !1;
    var i = l.firstBaseUpdate, o = l.lastBaseUpdate, d = l.shared.pending;
    if (d !== null) {
      l.shared.pending = null;
      var f = d, g = f.next;
      f.next = null, o === null ? i = g : o.next = g, o = f;
      var N = e.alternate;
      N !== null && (N = N.updateQueue, d = N.lastBaseUpdate, d !== o && (d === null ? N.firstBaseUpdate = g : d.next = g, N.lastBaseUpdate = f));
    }
    if (i !== null) {
      var z = l.baseState;
      o = 0, N = g = f = null, d = i;
      do {
        var j = d.lane, O = d.eventTime;
        if ((r & j) === j) {
          N !== null && (N = N.next = {
            eventTime: O,
            lane: 0,
            tag: d.tag,
            payload: d.payload,
            callback: d.callback,
            next: null
          });
          e: {
            var I = e, W = d;
            switch (j = n, O = t, W.tag) {
              case 1:
                if (I = W.payload, typeof I == "function") {
                  z = I.call(O, z, j);
                  break e;
                }
                z = I;
                break e;
              case 3:
                I.flags = I.flags & -65537 | 128;
              case 0:
                if (I = W.payload, j = typeof I == "function" ? I.call(O, z, j) : I, j == null) break e;
                z = P({}, z, j);
                break e;
              case 2:
                Zn = !0;
            }
          }
          d.callback !== null && d.lane !== 0 && (e.flags |= 64, j = l.effects, j === null ? l.effects = [d] : j.push(d));
        } else O = { eventTime: O, lane: j, tag: d.tag, payload: d.payload, callback: d.callback, next: null }, N === null ? (g = N = O, f = z) : N = N.next = O, o |= j;
        if (d = d.next, d === null) {
          if (d = l.shared.pending, d === null) break;
          j = d, d = j.next, j.next = null, l.lastBaseUpdate = j, l.shared.pending = null;
        }
      } while (!0);
      if (N === null && (f = z), l.baseState = f, l.firstBaseUpdate = g, l.lastBaseUpdate = N, n = l.shared.interleaved, n !== null) {
        l = n;
        do
          o |= l.lane, l = l.next;
        while (l !== n);
      } else i === null && (l.shared.lanes = 0);
      ut |= o, e.lanes = o, e.memoizedState = z;
    }
  }
  function ju(e, n, t) {
    if (e = n.effects, n.effects = null, e !== null) for (n = 0; n < e.length; n++) {
      var r = e[n], l = r.callback;
      if (l !== null) {
        if (r.callback = null, r = t, typeof l != "function") throw Error(c(191, l));
        l.call(r);
      }
    }
  }
  var dr = {}, En = An(dr), fr = An(dr), pr = An(dr);
  function ot(e) {
    if (e === dr) throw Error(c(174));
    return e;
  }
  function Ji(e, n) {
    switch (ie(pr, n), ie(fr, e), ie(En, dr), e = n.nodeType, e) {
      case 9:
      case 11:
        n = (n = n.documentElement) ? n.namespaceURI : Kl(null, "");
        break;
      default:
        e = e === 8 ? n.parentNode : n, n = e.namespaceURI || null, e = e.tagName, n = Kl(n, e);
    }
    ae(En), ie(En, n);
  }
  function Ft() {
    ae(En), ae(fr), ae(pr);
  }
  function Eu(e) {
    ot(pr.current);
    var n = ot(En.current), t = Kl(n, e.type);
    n !== t && (ie(fr, e), ie(En, t));
  }
  function Ki(e) {
    fr.current === e && (ae(En), ae(fr));
  }
  var me = An(0);
  function dl(e) {
    for (var n = e; n !== null; ) {
      if (n.tag === 13) {
        var t = n.memoizedState;
        if (t !== null && (t = t.dehydrated, t === null || t.data === "$?" || t.data === "$!")) return n;
      } else if (n.tag === 19 && n.memoizedProps.revealOrder !== void 0) {
        if ((n.flags & 128) !== 0) return n;
      } else if (n.child !== null) {
        n.child.return = n, n = n.child;
        continue;
      }
      if (n === e) break;
      for (; n.sibling === null; ) {
        if (n.return === null || n.return === e) return null;
        n = n.return;
      }
      n.sibling.return = n.return, n = n.sibling;
    }
    return null;
  }
  var Qi = [];
  function Gi() {
    for (var e = 0; e < Qi.length; e++) Qi[e]._workInProgressVersionPrimary = null;
    Qi.length = 0;
  }
  var fl = de.ReactCurrentDispatcher, Yi = de.ReactCurrentBatchConfig, st = 0, ve = null, Ce = null, Pe = null, pl = !1, hr = !1, mr = 0, Rd = 0;
  function Ue() {
    throw Error(c(321));
  }
  function _i(e, n) {
    if (n === null) return !1;
    for (var t = 0; t < n.length && t < e.length; t++) if (!hn(e[t], n[t])) return !1;
    return !0;
  }
  function bi(e, n, t, r, l, i) {
    if (st = i, ve = n, n.memoizedState = null, n.updateQueue = null, n.lanes = 0, fl.current = e === null || e.memoizedState === null ? Od : Fd, e = t(r, l), hr) {
      i = 0;
      do {
        if (hr = !1, mr = 0, 25 <= i) throw Error(c(301));
        i += 1, Pe = Ce = null, n.updateQueue = null, fl.current = Md, e = t(r, l);
      } while (hr);
    }
    if (fl.current = vl, n = Ce !== null && Ce.next !== null, st = 0, Pe = Ce = ve = null, pl = !1, n) throw Error(c(300));
    return e;
  }
  function $i() {
    var e = mr !== 0;
    return mr = 0, e;
  }
  function Nn() {
    var e = { memoizedState: null, baseState: null, baseQueue: null, queue: null, next: null };
    return Pe === null ? ve.memoizedState = Pe = e : Pe = Pe.next = e, Pe;
  }
  function cn() {
    if (Ce === null) {
      var e = ve.alternate;
      e = e !== null ? e.memoizedState : null;
    } else e = Ce.next;
    var n = Pe === null ? ve.memoizedState : Pe.next;
    if (n !== null) Pe = n, Ce = e;
    else {
      if (e === null) throw Error(c(310));
      Ce = e, e = { memoizedState: Ce.memoizedState, baseState: Ce.baseState, baseQueue: Ce.baseQueue, queue: Ce.queue, next: null }, Pe === null ? ve.memoizedState = Pe = e : Pe = Pe.next = e;
    }
    return Pe;
  }
  function vr(e, n) {
    return typeof n == "function" ? n(e) : n;
  }
  function eo(e) {
    var n = cn(), t = n.queue;
    if (t === null) throw Error(c(311));
    t.lastRenderedReducer = e;
    var r = Ce, l = r.baseQueue, i = t.pending;
    if (i !== null) {
      if (l !== null) {
        var o = l.next;
        l.next = i.next, i.next = o;
      }
      r.baseQueue = l = i, t.pending = null;
    }
    if (l !== null) {
      i = l.next, r = r.baseState;
      var d = o = null, f = null, g = i;
      do {
        var N = g.lane;
        if ((st & N) === N) f !== null && (f = f.next = { lane: 0, action: g.action, hasEagerState: g.hasEagerState, eagerState: g.eagerState, next: null }), r = g.hasEagerState ? g.eagerState : e(r, g.action);
        else {
          var z = {
            lane: N,
            action: g.action,
            hasEagerState: g.hasEagerState,
            eagerState: g.eagerState,
            next: null
          };
          f === null ? (d = f = z, o = r) : f = f.next = z, ve.lanes |= N, ut |= N;
        }
        g = g.next;
      } while (g !== null && g !== i);
      f === null ? o = r : f.next = d, hn(r, n.memoizedState) || (Qe = !0), n.memoizedState = r, n.baseState = o, n.baseQueue = f, t.lastRenderedState = r;
    }
    if (e = t.interleaved, e !== null) {
      l = e;
      do
        i = l.lane, ve.lanes |= i, ut |= i, l = l.next;
      while (l !== e);
    } else l === null && (t.lanes = 0);
    return [n.memoizedState, t.dispatch];
  }
  function no(e) {
    var n = cn(), t = n.queue;
    if (t === null) throw Error(c(311));
    t.lastRenderedReducer = e;
    var r = t.dispatch, l = t.pending, i = n.memoizedState;
    if (l !== null) {
      t.pending = null;
      var o = l = l.next;
      do
        i = e(i, o.action), o = o.next;
      while (o !== l);
      hn(i, n.memoizedState) || (Qe = !0), n.memoizedState = i, n.baseQueue === null && (n.baseState = i), t.lastRenderedState = i;
    }
    return [i, r];
  }
  function Nu() {
  }
  function zu(e, n) {
    var t = ve, r = cn(), l = n(), i = !hn(r.memoizedState, l);
    if (i && (r.memoizedState = l, Qe = !0), r = r.queue, to(Pu.bind(null, t, r, e), [e]), r.getSnapshot !== n || i || Pe !== null && Pe.memoizedState.tag & 1) {
      if (t.flags |= 2048, gr(9, Ru.bind(null, t, r, l, n), void 0, null), Te === null) throw Error(c(349));
      (st & 30) !== 0 || Cu(t, n, l);
    }
    return l;
  }
  function Cu(e, n, t) {
    e.flags |= 16384, e = { getSnapshot: n, value: t }, n = ve.updateQueue, n === null ? (n = { lastEffect: null, stores: null }, ve.updateQueue = n, n.stores = [e]) : (t = n.stores, t === null ? n.stores = [e] : t.push(e));
  }
  function Ru(e, n, t, r) {
    n.value = t, n.getSnapshot = r, Tu(n) && Lu(e);
  }
  function Pu(e, n, t) {
    return t(function() {
      Tu(n) && Lu(e);
    });
  }
  function Tu(e) {
    var n = e.getSnapshot;
    e = e.value;
    try {
      var t = n();
      return !hn(e, t);
    } catch {
      return !0;
    }
  }
  function Lu(e) {
    var n = Ln(e, 1);
    n !== null && xn(n, e, 1, -1);
  }
  function Ou(e) {
    var n = Nn();
    return typeof e == "function" && (e = e()), n.memoizedState = n.baseState = e, e = { pending: null, interleaved: null, lanes: 0, dispatch: null, lastRenderedReducer: vr, lastRenderedState: e }, n.queue = e, e = e.dispatch = Ld.bind(null, ve, e), [n.memoizedState, e];
  }
  function gr(e, n, t, r) {
    return e = { tag: e, create: n, destroy: t, deps: r, next: null }, n = ve.updateQueue, n === null ? (n = { lastEffect: null, stores: null }, ve.updateQueue = n, n.lastEffect = e.next = e) : (t = n.lastEffect, t === null ? n.lastEffect = e.next = e : (r = t.next, t.next = e, e.next = r, n.lastEffect = e)), e;
  }
  function Fu() {
    return cn().memoizedState;
  }
  function hl(e, n, t, r) {
    var l = Nn();
    ve.flags |= e, l.memoizedState = gr(1 | n, t, void 0, r === void 0 ? null : r);
  }
  function ml(e, n, t, r) {
    var l = cn();
    r = r === void 0 ? null : r;
    var i = void 0;
    if (Ce !== null) {
      var o = Ce.memoizedState;
      if (i = o.destroy, r !== null && _i(r, o.deps)) {
        l.memoizedState = gr(n, t, i, r);
        return;
      }
    }
    ve.flags |= e, l.memoizedState = gr(1 | n, t, i, r);
  }
  function Mu(e, n) {
    return hl(8390656, 8, e, n);
  }
  function to(e, n) {
    return ml(2048, 8, e, n);
  }
  function Iu(e, n) {
    return ml(4, 2, e, n);
  }
  function Wu(e, n) {
    return ml(4, 4, e, n);
  }
  function Du(e, n) {
    if (typeof n == "function") return e = e(), n(e), function() {
      n(null);
    };
    if (n != null) return e = e(), n.current = e, function() {
      n.current = null;
    };
  }
  function Vu(e, n, t) {
    return t = t != null ? t.concat([e]) : null, ml(4, 4, Du.bind(null, n, e), t);
  }
  function ro() {
  }
  function Uu(e, n) {
    var t = cn();
    n = n === void 0 ? null : n;
    var r = t.memoizedState;
    return r !== null && n !== null && _i(n, r[1]) ? r[0] : (t.memoizedState = [e, n], e);
  }
  function Hu(e, n) {
    var t = cn();
    n = n === void 0 ? null : n;
    var r = t.memoizedState;
    return r !== null && n !== null && _i(n, r[1]) ? r[0] : (e = e(), t.memoizedState = [e, n], e);
  }
  function qu(e, n, t) {
    return (st & 21) === 0 ? (e.baseState && (e.baseState = !1, Qe = !0), e.memoizedState = t) : (hn(t, n) || (t = gs(), ve.lanes |= t, ut |= t, e.baseState = !0), n);
  }
  function Pd(e, n) {
    var t = te;
    te = t !== 0 && 4 > t ? t : 4, e(!0);
    var r = Yi.transition;
    Yi.transition = {};
    try {
      e(!1), n();
    } finally {
      te = t, Yi.transition = r;
    }
  }
  function Au() {
    return cn().memoizedState;
  }
  function Td(e, n, t) {
    var r = Yn(e);
    if (t = { lane: r, action: t, hasEagerState: !1, eagerState: null, next: null }, Bu(e)) Xu(n, t);
    else if (t = wu(e, n, t, r), t !== null) {
      var l = Xe();
      xn(t, e, r, l), Zu(t, n, r);
    }
  }
  function Ld(e, n, t) {
    var r = Yn(e), l = { lane: r, action: t, hasEagerState: !1, eagerState: null, next: null };
    if (Bu(e)) Xu(n, l);
    else {
      var i = e.alternate;
      if (e.lanes === 0 && (i === null || i.lanes === 0) && (i = n.lastRenderedReducer, i !== null)) try {
        var o = n.lastRenderedState, d = i(o, t);
        if (l.hasEagerState = !0, l.eagerState = d, hn(d, o)) {
          var f = n.interleaved;
          f === null ? (l.next = l, Xi(n)) : (l.next = f.next, f.next = l), n.interleaved = l;
          return;
        }
      } catch {
      } finally {
      }
      t = wu(e, n, l, r), t !== null && (l = Xe(), xn(t, e, r, l), Zu(t, n, r));
    }
  }
  function Bu(e) {
    var n = e.alternate;
    return e === ve || n !== null && n === ve;
  }
  function Xu(e, n) {
    hr = pl = !0;
    var t = e.pending;
    t === null ? n.next = n : (n.next = t.next, t.next = n), e.pending = n;
  }
  function Zu(e, n, t) {
    if ((t & 4194240) !== 0) {
      var r = n.lanes;
      r &= e.pendingLanes, t |= r, n.lanes = t, ii(e, t);
    }
  }
  var vl = { readContext: an, useCallback: Ue, useContext: Ue, useEffect: Ue, useImperativeHandle: Ue, useInsertionEffect: Ue, useLayoutEffect: Ue, useMemo: Ue, useReducer: Ue, useRef: Ue, useState: Ue, useDebugValue: Ue, useDeferredValue: Ue, useTransition: Ue, useMutableSource: Ue, useSyncExternalStore: Ue, useId: Ue, unstable_isNewReconciler: !1 }, Od = { readContext: an, useCallback: function(e, n) {
    return Nn().memoizedState = [e, n === void 0 ? null : n], e;
  }, useContext: an, useEffect: Mu, useImperativeHandle: function(e, n, t) {
    return t = t != null ? t.concat([e]) : null, hl(
      4194308,
      4,
      Du.bind(null, n, e),
      t
    );
  }, useLayoutEffect: function(e, n) {
    return hl(4194308, 4, e, n);
  }, useInsertionEffect: function(e, n) {
    return hl(4, 2, e, n);
  }, useMemo: function(e, n) {
    var t = Nn();
    return n = n === void 0 ? null : n, e = e(), t.memoizedState = [e, n], e;
  }, useReducer: function(e, n, t) {
    var r = Nn();
    return n = t !== void 0 ? t(n) : n, r.memoizedState = r.baseState = n, e = { pending: null, interleaved: null, lanes: 0, dispatch: null, lastRenderedReducer: e, lastRenderedState: n }, r.queue = e, e = e.dispatch = Td.bind(null, ve, e), [r.memoizedState, e];
  }, useRef: function(e) {
    var n = Nn();
    return e = { current: e }, n.memoizedState = e;
  }, useState: Ou, useDebugValue: ro, useDeferredValue: function(e) {
    return Nn().memoizedState = e;
  }, useTransition: function() {
    var e = Ou(!1), n = e[0];
    return e = Pd.bind(null, e[1]), Nn().memoizedState = e, [n, e];
  }, useMutableSource: function() {
  }, useSyncExternalStore: function(e, n, t) {
    var r = ve, l = Nn();
    if (he) {
      if (t === void 0) throw Error(c(407));
      t = t();
    } else {
      if (t = n(), Te === null) throw Error(c(349));
      (st & 30) !== 0 || Cu(r, n, t);
    }
    l.memoizedState = t;
    var i = { value: t, getSnapshot: n };
    return l.queue = i, Mu(Pu.bind(
      null,
      r,
      i,
      e
    ), [e]), r.flags |= 2048, gr(9, Ru.bind(null, r, i, t, n), void 0, null), t;
  }, useId: function() {
    var e = Nn(), n = Te.identifierPrefix;
    if (he) {
      var t = Tn, r = Pn;
      t = (r & ~(1 << 32 - pn(r) - 1)).toString(32) + t, n = ":" + n + "R" + t, t = mr++, 0 < t && (n += "H" + t.toString(32)), n += ":";
    } else t = Rd++, n = ":" + n + "r" + t.toString(32) + ":";
    return e.memoizedState = n;
  }, unstable_isNewReconciler: !1 }, Fd = {
    readContext: an,
    useCallback: Uu,
    useContext: an,
    useEffect: to,
    useImperativeHandle: Vu,
    useInsertionEffect: Iu,
    useLayoutEffect: Wu,
    useMemo: Hu,
    useReducer: eo,
    useRef: Fu,
    useState: function() {
      return eo(vr);
    },
    useDebugValue: ro,
    useDeferredValue: function(e) {
      var n = cn();
      return qu(n, Ce.memoizedState, e);
    },
    useTransition: function() {
      var e = eo(vr)[0], n = cn().memoizedState;
      return [e, n];
    },
    useMutableSource: Nu,
    useSyncExternalStore: zu,
    useId: Au,
    unstable_isNewReconciler: !1
  }, Md = { readContext: an, useCallback: Uu, useContext: an, useEffect: to, useImperativeHandle: Vu, useInsertionEffect: Iu, useLayoutEffect: Wu, useMemo: Hu, useReducer: no, useRef: Fu, useState: function() {
    return no(vr);
  }, useDebugValue: ro, useDeferredValue: function(e) {
    var n = cn();
    return Ce === null ? n.memoizedState = e : qu(n, Ce.memoizedState, e);
  }, useTransition: function() {
    var e = no(vr)[0], n = cn().memoizedState;
    return [e, n];
  }, useMutableSource: Nu, useSyncExternalStore: zu, useId: Au, unstable_isNewReconciler: !1 };
  function vn(e, n) {
    if (e && e.defaultProps) {
      n = P({}, n), e = e.defaultProps;
      for (var t in e) n[t] === void 0 && (n[t] = e[t]);
      return n;
    }
    return n;
  }
  function lo(e, n, t, r) {
    n = e.memoizedState, t = t(r, n), t = t == null ? n : P({}, n, t), e.memoizedState = t, e.lanes === 0 && (e.updateQueue.baseState = t);
  }
  var gl = { isMounted: function(e) {
    return (e = e._reactInternals) ? et(e) === e : !1;
  }, enqueueSetState: function(e, n, t) {
    e = e._reactInternals;
    var r = Xe(), l = Yn(e), i = On(r, l);
    i.payload = n, t != null && (i.callback = t), n = Jn(e, i, l), n !== null && (xn(n, e, l, r), al(n, e, l));
  }, enqueueReplaceState: function(e, n, t) {
    e = e._reactInternals;
    var r = Xe(), l = Yn(e), i = On(r, l);
    i.tag = 1, i.payload = n, t != null && (i.callback = t), n = Jn(e, i, l), n !== null && (xn(n, e, l, r), al(n, e, l));
  }, enqueueForceUpdate: function(e, n) {
    e = e._reactInternals;
    var t = Xe(), r = Yn(e), l = On(t, r);
    l.tag = 2, n != null && (l.callback = n), n = Jn(e, l, r), n !== null && (xn(n, e, r, t), al(n, e, r));
  } };
  function Ju(e, n, t, r, l, i, o) {
    return e = e.stateNode, typeof e.shouldComponentUpdate == "function" ? e.shouldComponentUpdate(r, i, o) : n.prototype && n.prototype.isPureReactComponent ? !rr(t, r) || !rr(l, i) : !0;
  }
  function Ku(e, n, t) {
    var r = !1, l = Bn, i = n.contextType;
    return typeof i == "object" && i !== null ? i = an(i) : (l = Ke(n) ? tt : Ve.current, r = n.contextTypes, i = (r = r != null) ? zt(e, l) : Bn), n = new n(t, i), e.memoizedState = n.state !== null && n.state !== void 0 ? n.state : null, n.updater = gl, e.stateNode = n, n._reactInternals = e, r && (e = e.stateNode, e.__reactInternalMemoizedUnmaskedChildContext = l, e.__reactInternalMemoizedMaskedChildContext = i), n;
  }
  function Qu(e, n, t, r) {
    e = n.state, typeof n.componentWillReceiveProps == "function" && n.componentWillReceiveProps(t, r), typeof n.UNSAFE_componentWillReceiveProps == "function" && n.UNSAFE_componentWillReceiveProps(t, r), n.state !== e && gl.enqueueReplaceState(n, n.state, null);
  }
  function io(e, n, t, r) {
    var l = e.stateNode;
    l.props = t, l.state = e.memoizedState, l.refs = {}, Zi(e);
    var i = n.contextType;
    typeof i == "object" && i !== null ? l.context = an(i) : (i = Ke(n) ? tt : Ve.current, l.context = zt(e, i)), l.state = e.memoizedState, i = n.getDerivedStateFromProps, typeof i == "function" && (lo(e, n, i, t), l.state = e.memoizedState), typeof n.getDerivedStateFromProps == "function" || typeof l.getSnapshotBeforeUpdate == "function" || typeof l.UNSAFE_componentWillMount != "function" && typeof l.componentWillMount != "function" || (n = l.state, typeof l.componentWillMount == "function" && l.componentWillMount(), typeof l.UNSAFE_componentWillMount == "function" && l.UNSAFE_componentWillMount(), n !== l.state && gl.enqueueReplaceState(l, l.state, null), cl(e, t, l, r), l.state = e.memoizedState), typeof l.componentDidMount == "function" && (e.flags |= 4194308);
  }
  function Mt(e, n) {
    try {
      var t = "", r = n;
      do
        t += _(r), r = r.return;
      while (r);
      var l = t;
    } catch (i) {
      l = `
Error generating stack: ` + i.message + `
` + i.stack;
    }
    return { value: e, source: n, stack: l, digest: null };
  }
  function oo(e, n, t) {
    return { value: e, source: null, stack: t ?? null, digest: n ?? null };
  }
  function so(e, n) {
    try {
      console.error(n.value);
    } catch (t) {
      setTimeout(function() {
        throw t;
      });
    }
  }
  var Id = typeof WeakMap == "function" ? WeakMap : Map;
  function Gu(e, n, t) {
    t = On(-1, t), t.tag = 3, t.payload = { element: null };
    var r = n.value;
    return t.callback = function() {
      El || (El = !0, jo = r), so(e, n);
    }, t;
  }
  function Yu(e, n, t) {
    t = On(-1, t), t.tag = 3;
    var r = e.type.getDerivedStateFromError;
    if (typeof r == "function") {
      var l = n.value;
      t.payload = function() {
        return r(l);
      }, t.callback = function() {
        so(e, n);
      };
    }
    var i = e.stateNode;
    return i !== null && typeof i.componentDidCatch == "function" && (t.callback = function() {
      so(e, n), typeof r != "function" && (Qn === null ? Qn = /* @__PURE__ */ new Set([this]) : Qn.add(this));
      var o = n.stack;
      this.componentDidCatch(n.value, { componentStack: o !== null ? o : "" });
    }), t;
  }
  function _u(e, n, t) {
    var r = e.pingCache;
    if (r === null) {
      r = e.pingCache = new Id();
      var l = /* @__PURE__ */ new Set();
      r.set(n, l);
    } else l = r.get(n), l === void 0 && (l = /* @__PURE__ */ new Set(), r.set(n, l));
    l.has(t) || (l.add(t), e = Gd.bind(null, e, n, t), n.then(e, e));
  }
  function bu(e) {
    do {
      var n;
      if ((n = e.tag === 13) && (n = e.memoizedState, n = n !== null ? n.dehydrated !== null : !0), n) return e;
      e = e.return;
    } while (e !== null);
    return null;
  }
  function $u(e, n, t, r, l) {
    return (e.mode & 1) === 0 ? (e === n ? e.flags |= 65536 : (e.flags |= 128, t.flags |= 131072, t.flags &= -52805, t.tag === 1 && (t.alternate === null ? t.tag = 17 : (n = On(-1, 1), n.tag = 2, Jn(t, n, 1))), t.lanes |= 1), e) : (e.flags |= 65536, e.lanes = l, e);
  }
  var Wd = de.ReactCurrentOwner, Qe = !1;
  function Be(e, n, t, r) {
    n.child = e === null ? xu(n, null, t, r) : Tt(n, e.child, t, r);
  }
  function ea(e, n, t, r, l) {
    t = t.render;
    var i = n.ref;
    return Ot(n, l), r = bi(e, n, t, r, i, l), t = $i(), e !== null && !Qe ? (n.updateQueue = e.updateQueue, n.flags &= -2053, e.lanes &= ~l, Fn(e, n, l)) : (he && t && Ii(n), n.flags |= 1, Be(e, n, r, l), n.child);
  }
  function na(e, n, t, r, l) {
    if (e === null) {
      var i = t.type;
      return typeof i == "function" && !To(i) && i.defaultProps === void 0 && t.compare === null && t.defaultProps === void 0 ? (n.tag = 15, n.type = i, ta(e, n, i, r, l)) : (e = Tl(t.type, null, r, n, n.mode, l), e.ref = n.ref, e.return = n, n.child = e);
    }
    if (i = e.child, (e.lanes & l) === 0) {
      var o = i.memoizedProps;
      if (t = t.compare, t = t !== null ? t : rr, t(o, r) && e.ref === n.ref) return Fn(e, n, l);
    }
    return n.flags |= 1, e = bn(i, r), e.ref = n.ref, e.return = n, n.child = e;
  }
  function ta(e, n, t, r, l) {
    if (e !== null) {
      var i = e.memoizedProps;
      if (rr(i, r) && e.ref === n.ref) if (Qe = !1, n.pendingProps = r = i, (e.lanes & l) !== 0) (e.flags & 131072) !== 0 && (Qe = !0);
      else return n.lanes = e.lanes, Fn(e, n, l);
    }
    return uo(e, n, t, r, l);
  }
  function ra(e, n, t) {
    var r = n.pendingProps, l = r.children, i = e !== null ? e.memoizedState : null;
    if (r.mode === "hidden") if ((n.mode & 1) === 0) n.memoizedState = { baseLanes: 0, cachePool: null, transitions: null }, ie(Wt, ln), ln |= t;
    else {
      if ((t & 1073741824) === 0) return e = i !== null ? i.baseLanes | t : t, n.lanes = n.childLanes = 1073741824, n.memoizedState = { baseLanes: e, cachePool: null, transitions: null }, n.updateQueue = null, ie(Wt, ln), ln |= e, null;
      n.memoizedState = { baseLanes: 0, cachePool: null, transitions: null }, r = i !== null ? i.baseLanes : t, ie(Wt, ln), ln |= r;
    }
    else i !== null ? (r = i.baseLanes | t, n.memoizedState = null) : r = t, ie(Wt, ln), ln |= r;
    return Be(e, n, l, t), n.child;
  }
  function la(e, n) {
    var t = n.ref;
    (e === null && t !== null || e !== null && e.ref !== t) && (n.flags |= 512, n.flags |= 2097152);
  }
  function uo(e, n, t, r, l) {
    var i = Ke(t) ? tt : Ve.current;
    return i = zt(n, i), Ot(n, l), t = bi(e, n, t, r, i, l), r = $i(), e !== null && !Qe ? (n.updateQueue = e.updateQueue, n.flags &= -2053, e.lanes &= ~l, Fn(e, n, l)) : (he && r && Ii(n), n.flags |= 1, Be(e, n, t, l), n.child);
  }
  function ia(e, n, t, r, l) {
    if (Ke(t)) {
      var i = !0;
      nl(n);
    } else i = !1;
    if (Ot(n, l), n.stateNode === null) xl(e, n), Ku(n, t, r), io(n, t, r, l), r = !0;
    else if (e === null) {
      var o = n.stateNode, d = n.memoizedProps;
      o.props = d;
      var f = o.context, g = t.contextType;
      typeof g == "object" && g !== null ? g = an(g) : (g = Ke(t) ? tt : Ve.current, g = zt(n, g));
      var N = t.getDerivedStateFromProps, z = typeof N == "function" || typeof o.getSnapshotBeforeUpdate == "function";
      z || typeof o.UNSAFE_componentWillReceiveProps != "function" && typeof o.componentWillReceiveProps != "function" || (d !== r || f !== g) && Qu(n, o, r, g), Zn = !1;
      var j = n.memoizedState;
      o.state = j, cl(n, r, o, l), f = n.memoizedState, d !== r || j !== f || Je.current || Zn ? (typeof N == "function" && (lo(n, t, N, r), f = n.memoizedState), (d = Zn || Ju(n, t, d, r, j, f, g)) ? (z || typeof o.UNSAFE_componentWillMount != "function" && typeof o.componentWillMount != "function" || (typeof o.componentWillMount == "function" && o.componentWillMount(), typeof o.UNSAFE_componentWillMount == "function" && o.UNSAFE_componentWillMount()), typeof o.componentDidMount == "function" && (n.flags |= 4194308)) : (typeof o.componentDidMount == "function" && (n.flags |= 4194308), n.memoizedProps = r, n.memoizedState = f), o.props = r, o.state = f, o.context = g, r = d) : (typeof o.componentDidMount == "function" && (n.flags |= 4194308), r = !1);
    } else {
      o = n.stateNode, ku(e, n), d = n.memoizedProps, g = n.type === n.elementType ? d : vn(n.type, d), o.props = g, z = n.pendingProps, j = o.context, f = t.contextType, typeof f == "object" && f !== null ? f = an(f) : (f = Ke(t) ? tt : Ve.current, f = zt(n, f));
      var O = t.getDerivedStateFromProps;
      (N = typeof O == "function" || typeof o.getSnapshotBeforeUpdate == "function") || typeof o.UNSAFE_componentWillReceiveProps != "function" && typeof o.componentWillReceiveProps != "function" || (d !== z || j !== f) && Qu(n, o, r, f), Zn = !1, j = n.memoizedState, o.state = j, cl(n, r, o, l);
      var I = n.memoizedState;
      d !== z || j !== I || Je.current || Zn ? (typeof O == "function" && (lo(n, t, O, r), I = n.memoizedState), (g = Zn || Ju(n, t, g, r, j, I, f) || !1) ? (N || typeof o.UNSAFE_componentWillUpdate != "function" && typeof o.componentWillUpdate != "function" || (typeof o.componentWillUpdate == "function" && o.componentWillUpdate(r, I, f), typeof o.UNSAFE_componentWillUpdate == "function" && o.UNSAFE_componentWillUpdate(r, I, f)), typeof o.componentDidUpdate == "function" && (n.flags |= 4), typeof o.getSnapshotBeforeUpdate == "function" && (n.flags |= 1024)) : (typeof o.componentDidUpdate != "function" || d === e.memoizedProps && j === e.memoizedState || (n.flags |= 4), typeof o.getSnapshotBeforeUpdate != "function" || d === e.memoizedProps && j === e.memoizedState || (n.flags |= 1024), n.memoizedProps = r, n.memoizedState = I), o.props = r, o.state = I, o.context = f, r = g) : (typeof o.componentDidUpdate != "function" || d === e.memoizedProps && j === e.memoizedState || (n.flags |= 4), typeof o.getSnapshotBeforeUpdate != "function" || d === e.memoizedProps && j === e.memoizedState || (n.flags |= 1024), r = !1);
    }
    return ao(e, n, t, r, i, l);
  }
  function ao(e, n, t, r, l, i) {
    la(e, n);
    var o = (n.flags & 128) !== 0;
    if (!r && !o) return l && cu(n, t, !1), Fn(e, n, i);
    r = n.stateNode, Wd.current = n;
    var d = o && typeof t.getDerivedStateFromError != "function" ? null : r.render();
    return n.flags |= 1, e !== null && o ? (n.child = Tt(n, e.child, null, i), n.child = Tt(n, null, d, i)) : Be(e, n, d, i), n.memoizedState = r.state, l && cu(n, t, !0), n.child;
  }
  function oa(e) {
    var n = e.stateNode;
    n.pendingContext ? uu(e, n.pendingContext, n.pendingContext !== n.context) : n.context && uu(e, n.context, !1), Ji(e, n.containerInfo);
  }
  function sa(e, n, t, r, l) {
    return Pt(), Ui(l), n.flags |= 256, Be(e, n, t, r), n.child;
  }
  var co = { dehydrated: null, treeContext: null, retryLane: 0 };
  function fo(e) {
    return { baseLanes: e, cachePool: null, transitions: null };
  }
  function ua(e, n, t) {
    var r = n.pendingProps, l = me.current, i = !1, o = (n.flags & 128) !== 0, d;
    if ((d = o) || (d = e !== null && e.memoizedState === null ? !1 : (l & 2) !== 0), d ? (i = !0, n.flags &= -129) : (e === null || e.memoizedState !== null) && (l |= 1), ie(me, l & 1), e === null)
      return Vi(n), e = n.memoizedState, e !== null && (e = e.dehydrated, e !== null) ? ((n.mode & 1) === 0 ? n.lanes = 1 : e.data === "$!" ? n.lanes = 8 : n.lanes = 1073741824, null) : (o = r.children, e = r.fallback, i ? (r = n.mode, i = n.child, o = { mode: "hidden", children: o }, (r & 1) === 0 && i !== null ? (i.childLanes = 0, i.pendingProps = o) : i = Ll(o, r, 0, null), e = ft(e, r, t, null), i.return = n, e.return = n, i.sibling = e, n.child = i, n.child.memoizedState = fo(t), n.memoizedState = co, e) : po(n, o));
    if (l = e.memoizedState, l !== null && (d = l.dehydrated, d !== null)) return Dd(e, n, o, r, d, l, t);
    if (i) {
      i = r.fallback, o = n.mode, l = e.child, d = l.sibling;
      var f = { mode: "hidden", children: r.children };
      return (o & 1) === 0 && n.child !== l ? (r = n.child, r.childLanes = 0, r.pendingProps = f, n.deletions = null) : (r = bn(l, f), r.subtreeFlags = l.subtreeFlags & 14680064), d !== null ? i = bn(d, i) : (i = ft(i, o, t, null), i.flags |= 2), i.return = n, r.return = n, r.sibling = i, n.child = r, r = i, i = n.child, o = e.child.memoizedState, o = o === null ? fo(t) : { baseLanes: o.baseLanes | t, cachePool: null, transitions: o.transitions }, i.memoizedState = o, i.childLanes = e.childLanes & ~t, n.memoizedState = co, r;
    }
    return i = e.child, e = i.sibling, r = bn(i, { mode: "visible", children: r.children }), (n.mode & 1) === 0 && (r.lanes = t), r.return = n, r.sibling = null, e !== null && (t = n.deletions, t === null ? (n.deletions = [e], n.flags |= 16) : t.push(e)), n.child = r, n.memoizedState = null, r;
  }
  function po(e, n) {
    return n = Ll({ mode: "visible", children: n }, e.mode, 0, null), n.return = e, e.child = n;
  }
  function yl(e, n, t, r) {
    return r !== null && Ui(r), Tt(n, e.child, null, t), e = po(n, n.pendingProps.children), e.flags |= 2, n.memoizedState = null, e;
  }
  function Dd(e, n, t, r, l, i, o) {
    if (t)
      return n.flags & 256 ? (n.flags &= -257, r = oo(Error(c(422))), yl(e, n, o, r)) : n.memoizedState !== null ? (n.child = e.child, n.flags |= 128, null) : (i = r.fallback, l = n.mode, r = Ll({ mode: "visible", children: r.children }, l, 0, null), i = ft(i, l, o, null), i.flags |= 2, r.return = n, i.return = n, r.sibling = i, n.child = r, (n.mode & 1) !== 0 && Tt(n, e.child, null, o), n.child.memoizedState = fo(o), n.memoizedState = co, i);
    if ((n.mode & 1) === 0) return yl(e, n, o, null);
    if (l.data === "$!") {
      if (r = l.nextSibling && l.nextSibling.dataset, r) var d = r.dgst;
      return r = d, i = Error(c(419)), r = oo(i, r, void 0), yl(e, n, o, r);
    }
    if (d = (o & e.childLanes) !== 0, Qe || d) {
      if (r = Te, r !== null) {
        switch (o & -o) {
          case 4:
            l = 2;
            break;
          case 16:
            l = 8;
            break;
          case 64:
          case 128:
          case 256:
          case 512:
          case 1024:
          case 2048:
          case 4096:
          case 8192:
          case 16384:
          case 32768:
          case 65536:
          case 131072:
          case 262144:
          case 524288:
          case 1048576:
          case 2097152:
          case 4194304:
          case 8388608:
          case 16777216:
          case 33554432:
          case 67108864:
            l = 32;
            break;
          case 536870912:
            l = 268435456;
            break;
          default:
            l = 0;
        }
        l = (l & (r.suspendedLanes | o)) !== 0 ? 0 : l, l !== 0 && l !== i.retryLane && (i.retryLane = l, Ln(e, l), xn(r, e, l, -1));
      }
      return Po(), r = oo(Error(c(421))), yl(e, n, o, r);
    }
    return l.data === "$?" ? (n.flags |= 128, n.child = e.child, n = Yd.bind(null, e), l._reactRetry = n, null) : (e = i.treeContext, rn = qn(l.nextSibling), tn = n, he = !0, mn = null, e !== null && (sn[un++] = Pn, sn[un++] = Tn, sn[un++] = rt, Pn = e.id, Tn = e.overflow, rt = n), n = po(n, r.children), n.flags |= 4096, n);
  }
  function aa(e, n, t) {
    e.lanes |= n;
    var r = e.alternate;
    r !== null && (r.lanes |= n), Bi(e.return, n, t);
  }
  function ho(e, n, t, r, l) {
    var i = e.memoizedState;
    i === null ? e.memoizedState = { isBackwards: n, rendering: null, renderingStartTime: 0, last: r, tail: t, tailMode: l } : (i.isBackwards = n, i.rendering = null, i.renderingStartTime = 0, i.last = r, i.tail = t, i.tailMode = l);
  }
  function ca(e, n, t) {
    var r = n.pendingProps, l = r.revealOrder, i = r.tail;
    if (Be(e, n, r.children, t), r = me.current, (r & 2) !== 0) r = r & 1 | 2, n.flags |= 128;
    else {
      if (e !== null && (e.flags & 128) !== 0) e: for (e = n.child; e !== null; ) {
        if (e.tag === 13) e.memoizedState !== null && aa(e, t, n);
        else if (e.tag === 19) aa(e, t, n);
        else if (e.child !== null) {
          e.child.return = e, e = e.child;
          continue;
        }
        if (e === n) break e;
        for (; e.sibling === null; ) {
          if (e.return === null || e.return === n) break e;
          e = e.return;
        }
        e.sibling.return = e.return, e = e.sibling;
      }
      r &= 1;
    }
    if (ie(me, r), (n.mode & 1) === 0) n.memoizedState = null;
    else switch (l) {
      case "forwards":
        for (t = n.child, l = null; t !== null; ) e = t.alternate, e !== null && dl(e) === null && (l = t), t = t.sibling;
        t = l, t === null ? (l = n.child, n.child = null) : (l = t.sibling, t.sibling = null), ho(n, !1, l, t, i);
        break;
      case "backwards":
        for (t = null, l = n.child, n.child = null; l !== null; ) {
          if (e = l.alternate, e !== null && dl(e) === null) {
            n.child = l;
            break;
          }
          e = l.sibling, l.sibling = t, t = l, l = e;
        }
        ho(n, !0, t, null, i);
        break;
      case "together":
        ho(n, !1, null, null, void 0);
        break;
      default:
        n.memoizedState = null;
    }
    return n.child;
  }
  function xl(e, n) {
    (n.mode & 1) === 0 && e !== null && (e.alternate = null, n.alternate = null, n.flags |= 2);
  }
  function Fn(e, n, t) {
    if (e !== null && (n.dependencies = e.dependencies), ut |= n.lanes, (t & n.childLanes) === 0) return null;
    if (e !== null && n.child !== e.child) throw Error(c(153));
    if (n.child !== null) {
      for (e = n.child, t = bn(e, e.pendingProps), n.child = t, t.return = n; e.sibling !== null; ) e = e.sibling, t = t.sibling = bn(e, e.pendingProps), t.return = n;
      t.sibling = null;
    }
    return n.child;
  }
  function Vd(e, n, t) {
    switch (n.tag) {
      case 3:
        oa(n), Pt();
        break;
      case 5:
        Eu(n);
        break;
      case 1:
        Ke(n.type) && nl(n);
        break;
      case 4:
        Ji(n, n.stateNode.containerInfo);
        break;
      case 10:
        var r = n.type._context, l = n.memoizedProps.value;
        ie(sl, r._currentValue), r._currentValue = l;
        break;
      case 13:
        if (r = n.memoizedState, r !== null)
          return r.dehydrated !== null ? (ie(me, me.current & 1), n.flags |= 128, null) : (t & n.child.childLanes) !== 0 ? ua(e, n, t) : (ie(me, me.current & 1), e = Fn(e, n, t), e !== null ? e.sibling : null);
        ie(me, me.current & 1);
        break;
      case 19:
        if (r = (t & n.childLanes) !== 0, (e.flags & 128) !== 0) {
          if (r) return ca(e, n, t);
          n.flags |= 128;
        }
        if (l = n.memoizedState, l !== null && (l.rendering = null, l.tail = null, l.lastEffect = null), ie(me, me.current), r) break;
        return null;
      case 22:
      case 23:
        return n.lanes = 0, ra(e, n, t);
    }
    return Fn(e, n, t);
  }
  var da, mo, fa, pa;
  da = function(e, n) {
    for (var t = n.child; t !== null; ) {
      if (t.tag === 5 || t.tag === 6) e.appendChild(t.stateNode);
      else if (t.tag !== 4 && t.child !== null) {
        t.child.return = t, t = t.child;
        continue;
      }
      if (t === n) break;
      for (; t.sibling === null; ) {
        if (t.return === null || t.return === n) return;
        t = t.return;
      }
      t.sibling.return = t.return, t = t.sibling;
    }
  }, mo = function() {
  }, fa = function(e, n, t, r) {
    var l = e.memoizedProps;
    if (l !== r) {
      e = n.stateNode, ot(En.current);
      var i = null;
      switch (t) {
        case "input":
          l = Bl(e, l), r = Bl(e, r), i = [];
          break;
        case "select":
          l = P({}, l, { value: void 0 }), r = P({}, r, { value: void 0 }), i = [];
          break;
        case "textarea":
          l = Jl(e, l), r = Jl(e, r), i = [];
          break;
        default:
          typeof l.onClick != "function" && typeof r.onClick == "function" && (e.onclick = br);
      }
      Ql(t, r);
      var o;
      t = null;
      for (g in l) if (!r.hasOwnProperty(g) && l.hasOwnProperty(g) && l[g] != null) if (g === "style") {
        var d = l[g];
        for (o in d) d.hasOwnProperty(o) && (t || (t = {}), t[o] = "");
      } else g !== "dangerouslySetInnerHTML" && g !== "children" && g !== "suppressContentEditableWarning" && g !== "suppressHydrationWarning" && g !== "autoFocus" && (x.hasOwnProperty(g) ? i || (i = []) : (i = i || []).push(g, null));
      for (g in r) {
        var f = r[g];
        if (d = l != null ? l[g] : void 0, r.hasOwnProperty(g) && f !== d && (f != null || d != null)) if (g === "style") if (d) {
          for (o in d) !d.hasOwnProperty(o) || f && f.hasOwnProperty(o) || (t || (t = {}), t[o] = "");
          for (o in f) f.hasOwnProperty(o) && d[o] !== f[o] && (t || (t = {}), t[o] = f[o]);
        } else t || (i || (i = []), i.push(
          g,
          t
        )), t = f;
        else g === "dangerouslySetInnerHTML" ? (f = f ? f.__html : void 0, d = d ? d.__html : void 0, f != null && d !== f && (i = i || []).push(g, f)) : g === "children" ? typeof f != "string" && typeof f != "number" || (i = i || []).push(g, "" + f) : g !== "suppressContentEditableWarning" && g !== "suppressHydrationWarning" && (x.hasOwnProperty(g) ? (f != null && g === "onScroll" && ue("scroll", e), i || d === f || (i = [])) : (i = i || []).push(g, f));
      }
      t && (i = i || []).push("style", t);
      var g = i;
      (n.updateQueue = g) && (n.flags |= 4);
    }
  }, pa = function(e, n, t, r) {
    t !== r && (n.flags |= 4);
  };
  function yr(e, n) {
    if (!he) switch (e.tailMode) {
      case "hidden":
        n = e.tail;
        for (var t = null; n !== null; ) n.alternate !== null && (t = n), n = n.sibling;
        t === null ? e.tail = null : t.sibling = null;
        break;
      case "collapsed":
        t = e.tail;
        for (var r = null; t !== null; ) t.alternate !== null && (r = t), t = t.sibling;
        r === null ? n || e.tail === null ? e.tail = null : e.tail.sibling = null : r.sibling = null;
    }
  }
  function He(e) {
    var n = e.alternate !== null && e.alternate.child === e.child, t = 0, r = 0;
    if (n) for (var l = e.child; l !== null; ) t |= l.lanes | l.childLanes, r |= l.subtreeFlags & 14680064, r |= l.flags & 14680064, l.return = e, l = l.sibling;
    else for (l = e.child; l !== null; ) t |= l.lanes | l.childLanes, r |= l.subtreeFlags, r |= l.flags, l.return = e, l = l.sibling;
    return e.subtreeFlags |= r, e.childLanes = t, n;
  }
  function Ud(e, n, t) {
    var r = n.pendingProps;
    switch (Wi(n), n.tag) {
      case 2:
      case 16:
      case 15:
      case 0:
      case 11:
      case 7:
      case 8:
      case 12:
      case 9:
      case 14:
        return He(n), null;
      case 1:
        return Ke(n.type) && el(), He(n), null;
      case 3:
        return r = n.stateNode, Ft(), ae(Je), ae(Ve), Gi(), r.pendingContext && (r.context = r.pendingContext, r.pendingContext = null), (e === null || e.child === null) && (il(n) ? n.flags |= 4 : e === null || e.memoizedState.isDehydrated && (n.flags & 256) === 0 || (n.flags |= 1024, mn !== null && (zo(mn), mn = null))), mo(e, n), He(n), null;
      case 5:
        Ki(n);
        var l = ot(pr.current);
        if (t = n.type, e !== null && n.stateNode != null) fa(e, n, t, r, l), e.ref !== n.ref && (n.flags |= 512, n.flags |= 2097152);
        else {
          if (!r) {
            if (n.stateNode === null) throw Error(c(166));
            return He(n), null;
          }
          if (e = ot(En.current), il(n)) {
            r = n.stateNode, t = n.type;
            var i = n.memoizedProps;
            switch (r[jn] = n, r[ur] = i, e = (n.mode & 1) !== 0, t) {
              case "dialog":
                ue("cancel", r), ue("close", r);
                break;
              case "iframe":
              case "object":
              case "embed":
                ue("load", r);
                break;
              case "video":
              case "audio":
                for (l = 0; l < ir.length; l++) ue(ir[l], r);
                break;
              case "source":
                ue("error", r);
                break;
              case "img":
              case "image":
              case "link":
                ue(
                  "error",
                  r
                ), ue("load", r);
                break;
              case "details":
                ue("toggle", r);
                break;
              case "input":
                Ko(r, i), ue("invalid", r);
                break;
              case "select":
                r._wrapperState = { wasMultiple: !!i.multiple }, ue("invalid", r);
                break;
              case "textarea":
                Yo(r, i), ue("invalid", r);
            }
            Ql(t, i), l = null;
            for (var o in i) if (i.hasOwnProperty(o)) {
              var d = i[o];
              o === "children" ? typeof d == "string" ? r.textContent !== d && (i.suppressHydrationWarning !== !0 && _r(r.textContent, d, e), l = ["children", d]) : typeof d == "number" && r.textContent !== "" + d && (i.suppressHydrationWarning !== !0 && _r(
                r.textContent,
                d,
                e
              ), l = ["children", "" + d]) : x.hasOwnProperty(o) && d != null && o === "onScroll" && ue("scroll", r);
            }
            switch (t) {
              case "input":
                Rr(r), Go(r, i, !0);
                break;
              case "textarea":
                Rr(r), bo(r);
                break;
              case "select":
              case "option":
                break;
              default:
                typeof i.onClick == "function" && (r.onclick = br);
            }
            r = l, n.updateQueue = r, r !== null && (n.flags |= 4);
          } else {
            o = l.nodeType === 9 ? l : l.ownerDocument, e === "http://www.w3.org/1999/xhtml" && (e = $o(t)), e === "http://www.w3.org/1999/xhtml" ? t === "script" ? (e = o.createElement("div"), e.innerHTML = "<script><\/script>", e = e.removeChild(e.firstChild)) : typeof r.is == "string" ? e = o.createElement(t, { is: r.is }) : (e = o.createElement(t), t === "select" && (o = e, r.multiple ? o.multiple = !0 : r.size && (o.size = r.size))) : e = o.createElementNS(e, t), e[jn] = n, e[ur] = r, da(e, n, !1, !1), n.stateNode = e;
            e: {
              switch (o = Gl(t, r), t) {
                case "dialog":
                  ue("cancel", e), ue("close", e), l = r;
                  break;
                case "iframe":
                case "object":
                case "embed":
                  ue("load", e), l = r;
                  break;
                case "video":
                case "audio":
                  for (l = 0; l < ir.length; l++) ue(ir[l], e);
                  l = r;
                  break;
                case "source":
                  ue("error", e), l = r;
                  break;
                case "img":
                case "image":
                case "link":
                  ue(
                    "error",
                    e
                  ), ue("load", e), l = r;
                  break;
                case "details":
                  ue("toggle", e), l = r;
                  break;
                case "input":
                  Ko(e, r), l = Bl(e, r), ue("invalid", e);
                  break;
                case "option":
                  l = r;
                  break;
                case "select":
                  e._wrapperState = { wasMultiple: !!r.multiple }, l = P({}, r, { value: void 0 }), ue("invalid", e);
                  break;
                case "textarea":
                  Yo(e, r), l = Jl(e, r), ue("invalid", e);
                  break;
                default:
                  l = r;
              }
              Ql(t, l), d = l;
              for (i in d) if (d.hasOwnProperty(i)) {
                var f = d[i];
                i === "style" ? ts(e, f) : i === "dangerouslySetInnerHTML" ? (f = f ? f.__html : void 0, f != null && es(e, f)) : i === "children" ? typeof f == "string" ? (t !== "textarea" || f !== "") && Ht(e, f) : typeof f == "number" && Ht(e, "" + f) : i !== "suppressContentEditableWarning" && i !== "suppressHydrationWarning" && i !== "autoFocus" && (x.hasOwnProperty(i) ? f != null && i === "onScroll" && ue("scroll", e) : f != null && Ne(e, i, f, o));
              }
              switch (t) {
                case "input":
                  Rr(e), Go(e, r, !1);
                  break;
                case "textarea":
                  Rr(e), bo(e);
                  break;
                case "option":
                  r.value != null && e.setAttribute("value", "" + ne(r.value));
                  break;
                case "select":
                  e.multiple = !!r.multiple, i = r.value, i != null ? ht(e, !!r.multiple, i, !1) : r.defaultValue != null && ht(
                    e,
                    !!r.multiple,
                    r.defaultValue,
                    !0
                  );
                  break;
                default:
                  typeof l.onClick == "function" && (e.onclick = br);
              }
              switch (t) {
                case "button":
                case "input":
                case "select":
                case "textarea":
                  r = !!r.autoFocus;
                  break e;
                case "img":
                  r = !0;
                  break e;
                default:
                  r = !1;
              }
            }
            r && (n.flags |= 4);
          }
          n.ref !== null && (n.flags |= 512, n.flags |= 2097152);
        }
        return He(n), null;
      case 6:
        if (e && n.stateNode != null) pa(e, n, e.memoizedProps, r);
        else {
          if (typeof r != "string" && n.stateNode === null) throw Error(c(166));
          if (t = ot(pr.current), ot(En.current), il(n)) {
            if (r = n.stateNode, t = n.memoizedProps, r[jn] = n, (i = r.nodeValue !== t) && (e = tn, e !== null)) switch (e.tag) {
              case 3:
                _r(r.nodeValue, t, (e.mode & 1) !== 0);
                break;
              case 5:
                e.memoizedProps.suppressHydrationWarning !== !0 && _r(r.nodeValue, t, (e.mode & 1) !== 0);
            }
            i && (n.flags |= 4);
          } else r = (t.nodeType === 9 ? t : t.ownerDocument).createTextNode(r), r[jn] = n, n.stateNode = r;
        }
        return He(n), null;
      case 13:
        if (ae(me), r = n.memoizedState, e === null || e.memoizedState !== null && e.memoizedState.dehydrated !== null) {
          if (he && rn !== null && (n.mode & 1) !== 0 && (n.flags & 128) === 0) vu(), Pt(), n.flags |= 98560, i = !1;
          else if (i = il(n), r !== null && r.dehydrated !== null) {
            if (e === null) {
              if (!i) throw Error(c(318));
              if (i = n.memoizedState, i = i !== null ? i.dehydrated : null, !i) throw Error(c(317));
              i[jn] = n;
            } else Pt(), (n.flags & 128) === 0 && (n.memoizedState = null), n.flags |= 4;
            He(n), i = !1;
          } else mn !== null && (zo(mn), mn = null), i = !0;
          if (!i) return n.flags & 65536 ? n : null;
        }
        return (n.flags & 128) !== 0 ? (n.lanes = t, n) : (r = r !== null, r !== (e !== null && e.memoizedState !== null) && r && (n.child.flags |= 8192, (n.mode & 1) !== 0 && (e === null || (me.current & 1) !== 0 ? Re === 0 && (Re = 3) : Po())), n.updateQueue !== null && (n.flags |= 4), He(n), null);
      case 4:
        return Ft(), mo(e, n), e === null && or(n.stateNode.containerInfo), He(n), null;
      case 10:
        return Ai(n.type._context), He(n), null;
      case 17:
        return Ke(n.type) && el(), He(n), null;
      case 19:
        if (ae(me), i = n.memoizedState, i === null) return He(n), null;
        if (r = (n.flags & 128) !== 0, o = i.rendering, o === null) if (r) yr(i, !1);
        else {
          if (Re !== 0 || e !== null && (e.flags & 128) !== 0) for (e = n.child; e !== null; ) {
            if (o = dl(e), o !== null) {
              for (n.flags |= 128, yr(i, !1), r = o.updateQueue, r !== null && (n.updateQueue = r, n.flags |= 4), n.subtreeFlags = 0, r = t, t = n.child; t !== null; ) i = t, e = r, i.flags &= 14680066, o = i.alternate, o === null ? (i.childLanes = 0, i.lanes = e, i.child = null, i.subtreeFlags = 0, i.memoizedProps = null, i.memoizedState = null, i.updateQueue = null, i.dependencies = null, i.stateNode = null) : (i.childLanes = o.childLanes, i.lanes = o.lanes, i.child = o.child, i.subtreeFlags = 0, i.deletions = null, i.memoizedProps = o.memoizedProps, i.memoizedState = o.memoizedState, i.updateQueue = o.updateQueue, i.type = o.type, e = o.dependencies, i.dependencies = e === null ? null : { lanes: e.lanes, firstContext: e.firstContext }), t = t.sibling;
              return ie(me, me.current & 1 | 2), n.child;
            }
            e = e.sibling;
          }
          i.tail !== null && we() > Dt && (n.flags |= 128, r = !0, yr(i, !1), n.lanes = 4194304);
        }
        else {
          if (!r) if (e = dl(o), e !== null) {
            if (n.flags |= 128, r = !0, t = e.updateQueue, t !== null && (n.updateQueue = t, n.flags |= 4), yr(i, !0), i.tail === null && i.tailMode === "hidden" && !o.alternate && !he) return He(n), null;
          } else 2 * we() - i.renderingStartTime > Dt && t !== 1073741824 && (n.flags |= 128, r = !0, yr(i, !1), n.lanes = 4194304);
          i.isBackwards ? (o.sibling = n.child, n.child = o) : (t = i.last, t !== null ? t.sibling = o : n.child = o, i.last = o);
        }
        return i.tail !== null ? (n = i.tail, i.rendering = n, i.tail = n.sibling, i.renderingStartTime = we(), n.sibling = null, t = me.current, ie(me, r ? t & 1 | 2 : t & 1), n) : (He(n), null);
      case 22:
      case 23:
        return Ro(), r = n.memoizedState !== null, e !== null && e.memoizedState !== null !== r && (n.flags |= 8192), r && (n.mode & 1) !== 0 ? (ln & 1073741824) !== 0 && (He(n), n.subtreeFlags & 6 && (n.flags |= 8192)) : He(n), null;
      case 24:
        return null;
      case 25:
        return null;
    }
    throw Error(c(156, n.tag));
  }
  function Hd(e, n) {
    switch (Wi(n), n.tag) {
      case 1:
        return Ke(n.type) && el(), e = n.flags, e & 65536 ? (n.flags = e & -65537 | 128, n) : null;
      case 3:
        return Ft(), ae(Je), ae(Ve), Gi(), e = n.flags, (e & 65536) !== 0 && (e & 128) === 0 ? (n.flags = e & -65537 | 128, n) : null;
      case 5:
        return Ki(n), null;
      case 13:
        if (ae(me), e = n.memoizedState, e !== null && e.dehydrated !== null) {
          if (n.alternate === null) throw Error(c(340));
          Pt();
        }
        return e = n.flags, e & 65536 ? (n.flags = e & -65537 | 128, n) : null;
      case 19:
        return ae(me), null;
      case 4:
        return Ft(), null;
      case 10:
        return Ai(n.type._context), null;
      case 22:
      case 23:
        return Ro(), null;
      case 24:
        return null;
      default:
        return null;
    }
  }
  var wl = !1, qe = !1, qd = typeof WeakSet == "function" ? WeakSet : Set, M = null;
  function It(e, n) {
    var t = e.ref;
    if (t !== null) if (typeof t == "function") try {
      t(null);
    } catch (r) {
      xe(e, n, r);
    }
    else t.current = null;
  }
  function vo(e, n, t) {
    try {
      t();
    } catch (r) {
      xe(e, n, r);
    }
  }
  var ha = !1;
  function Ad(e, n) {
    if (Ci = Hr, e = Js(), xi(e)) {
      if ("selectionStart" in e) var t = { start: e.selectionStart, end: e.selectionEnd };
      else e: {
        t = (t = e.ownerDocument) && t.defaultView || window;
        var r = t.getSelection && t.getSelection();
        if (r && r.rangeCount !== 0) {
          t = r.anchorNode;
          var l = r.anchorOffset, i = r.focusNode;
          r = r.focusOffset;
          try {
            t.nodeType, i.nodeType;
          } catch {
            t = null;
            break e;
          }
          var o = 0, d = -1, f = -1, g = 0, N = 0, z = e, j = null;
          n: for (; ; ) {
            for (var O; z !== t || l !== 0 && z.nodeType !== 3 || (d = o + l), z !== i || r !== 0 && z.nodeType !== 3 || (f = o + r), z.nodeType === 3 && (o += z.nodeValue.length), (O = z.firstChild) !== null; )
              j = z, z = O;
            for (; ; ) {
              if (z === e) break n;
              if (j === t && ++g === l && (d = o), j === i && ++N === r && (f = o), (O = z.nextSibling) !== null) break;
              z = j, j = z.parentNode;
            }
            z = O;
          }
          t = d === -1 || f === -1 ? null : { start: d, end: f };
        } else t = null;
      }
      t = t || { start: 0, end: 0 };
    } else t = null;
    for (Ri = { focusedElem: e, selectionRange: t }, Hr = !1, M = n; M !== null; ) if (n = M, e = n.child, (n.subtreeFlags & 1028) !== 0 && e !== null) e.return = n, M = e;
    else for (; M !== null; ) {
      n = M;
      try {
        var I = n.alternate;
        if ((n.flags & 1024) !== 0) switch (n.tag) {
          case 0:
          case 11:
          case 15:
            break;
          case 1:
            if (I !== null) {
              var W = I.memoizedProps, ke = I.memoizedState, m = n.stateNode, p = m.getSnapshotBeforeUpdate(n.elementType === n.type ? W : vn(n.type, W), ke);
              m.__reactInternalSnapshotBeforeUpdate = p;
            }
            break;
          case 3:
            var v = n.stateNode.containerInfo;
            v.nodeType === 1 ? v.textContent = "" : v.nodeType === 9 && v.documentElement && v.removeChild(v.documentElement);
            break;
          case 5:
          case 6:
          case 4:
          case 17:
            break;
          default:
            throw Error(c(163));
        }
      } catch (C) {
        xe(n, n.return, C);
      }
      if (e = n.sibling, e !== null) {
        e.return = n.return, M = e;
        break;
      }
      M = n.return;
    }
    return I = ha, ha = !1, I;
  }
  function xr(e, n, t) {
    var r = n.updateQueue;
    if (r = r !== null ? r.lastEffect : null, r !== null) {
      var l = r = r.next;
      do {
        if ((l.tag & e) === e) {
          var i = l.destroy;
          l.destroy = void 0, i !== void 0 && vo(n, t, i);
        }
        l = l.next;
      } while (l !== r);
    }
  }
  function kl(e, n) {
    if (n = n.updateQueue, n = n !== null ? n.lastEffect : null, n !== null) {
      var t = n = n.next;
      do {
        if ((t.tag & e) === e) {
          var r = t.create;
          t.destroy = r();
        }
        t = t.next;
      } while (t !== n);
    }
  }
  function go(e) {
    var n = e.ref;
    if (n !== null) {
      var t = e.stateNode;
      switch (e.tag) {
        case 5:
          e = t;
          break;
        default:
          e = t;
      }
      typeof n == "function" ? n(e) : n.current = e;
    }
  }
  function ma(e) {
    var n = e.alternate;
    n !== null && (e.alternate = null, ma(n)), e.child = null, e.deletions = null, e.sibling = null, e.tag === 5 && (n = e.stateNode, n !== null && (delete n[jn], delete n[ur], delete n[Oi], delete n[Ed], delete n[Nd])), e.stateNode = null, e.return = null, e.dependencies = null, e.memoizedProps = null, e.memoizedState = null, e.pendingProps = null, e.stateNode = null, e.updateQueue = null;
  }
  function va(e) {
    return e.tag === 5 || e.tag === 3 || e.tag === 4;
  }
  function ga(e) {
    e: for (; ; ) {
      for (; e.sibling === null; ) {
        if (e.return === null || va(e.return)) return null;
        e = e.return;
      }
      for (e.sibling.return = e.return, e = e.sibling; e.tag !== 5 && e.tag !== 6 && e.tag !== 18; ) {
        if (e.flags & 2 || e.child === null || e.tag === 4) continue e;
        e.child.return = e, e = e.child;
      }
      if (!(e.flags & 2)) return e.stateNode;
    }
  }
  function yo(e, n, t) {
    var r = e.tag;
    if (r === 5 || r === 6) e = e.stateNode, n ? t.nodeType === 8 ? t.parentNode.insertBefore(e, n) : t.insertBefore(e, n) : (t.nodeType === 8 ? (n = t.parentNode, n.insertBefore(e, t)) : (n = t, n.appendChild(e)), t = t._reactRootContainer, t != null || n.onclick !== null || (n.onclick = br));
    else if (r !== 4 && (e = e.child, e !== null)) for (yo(e, n, t), e = e.sibling; e !== null; ) yo(e, n, t), e = e.sibling;
  }
  function xo(e, n, t) {
    var r = e.tag;
    if (r === 5 || r === 6) e = e.stateNode, n ? t.insertBefore(e, n) : t.appendChild(e);
    else if (r !== 4 && (e = e.child, e !== null)) for (xo(e, n, t), e = e.sibling; e !== null; ) xo(e, n, t), e = e.sibling;
  }
  var Fe = null, gn = !1;
  function Kn(e, n, t) {
    for (t = t.child; t !== null; ) ya(e, n, t), t = t.sibling;
  }
  function ya(e, n, t) {
    if (Sn && typeof Sn.onCommitFiberUnmount == "function") try {
      Sn.onCommitFiberUnmount(Mr, t);
    } catch {
    }
    switch (t.tag) {
      case 5:
        qe || It(t, n);
      case 6:
        var r = Fe, l = gn;
        Fe = null, Kn(e, n, t), Fe = r, gn = l, Fe !== null && (gn ? (e = Fe, t = t.stateNode, e.nodeType === 8 ? e.parentNode.removeChild(t) : e.removeChild(t)) : Fe.removeChild(t.stateNode));
        break;
      case 18:
        Fe !== null && (gn ? (e = Fe, t = t.stateNode, e.nodeType === 8 ? Li(e.parentNode, t) : e.nodeType === 1 && Li(e, t), _t(e)) : Li(Fe, t.stateNode));
        break;
      case 4:
        r = Fe, l = gn, Fe = t.stateNode.containerInfo, gn = !0, Kn(e, n, t), Fe = r, gn = l;
        break;
      case 0:
      case 11:
      case 14:
      case 15:
        if (!qe && (r = t.updateQueue, r !== null && (r = r.lastEffect, r !== null))) {
          l = r = r.next;
          do {
            var i = l, o = i.destroy;
            i = i.tag, o !== void 0 && ((i & 2) !== 0 || (i & 4) !== 0) && vo(t, n, o), l = l.next;
          } while (l !== r);
        }
        Kn(e, n, t);
        break;
      case 1:
        if (!qe && (It(t, n), r = t.stateNode, typeof r.componentWillUnmount == "function")) try {
          r.props = t.memoizedProps, r.state = t.memoizedState, r.componentWillUnmount();
        } catch (d) {
          xe(t, n, d);
        }
        Kn(e, n, t);
        break;
      case 21:
        Kn(e, n, t);
        break;
      case 22:
        t.mode & 1 ? (qe = (r = qe) || t.memoizedState !== null, Kn(e, n, t), qe = r) : Kn(e, n, t);
        break;
      default:
        Kn(e, n, t);
    }
  }
  function xa(e) {
    var n = e.updateQueue;
    if (n !== null) {
      e.updateQueue = null;
      var t = e.stateNode;
      t === null && (t = e.stateNode = new qd()), n.forEach(function(r) {
        var l = _d.bind(null, e, r);
        t.has(r) || (t.add(r), r.then(l, l));
      });
    }
  }
  function yn(e, n) {
    var t = n.deletions;
    if (t !== null) for (var r = 0; r < t.length; r++) {
      var l = t[r];
      try {
        var i = e, o = n, d = o;
        e: for (; d !== null; ) {
          switch (d.tag) {
            case 5:
              Fe = d.stateNode, gn = !1;
              break e;
            case 3:
              Fe = d.stateNode.containerInfo, gn = !0;
              break e;
            case 4:
              Fe = d.stateNode.containerInfo, gn = !0;
              break e;
          }
          d = d.return;
        }
        if (Fe === null) throw Error(c(160));
        ya(i, o, l), Fe = null, gn = !1;
        var f = l.alternate;
        f !== null && (f.return = null), l.return = null;
      } catch (g) {
        xe(l, n, g);
      }
    }
    if (n.subtreeFlags & 12854) for (n = n.child; n !== null; ) wa(n, e), n = n.sibling;
  }
  function wa(e, n) {
    var t = e.alternate, r = e.flags;
    switch (e.tag) {
      case 0:
      case 11:
      case 14:
      case 15:
        if (yn(n, e), zn(e), r & 4) {
          try {
            xr(3, e, e.return), kl(3, e);
          } catch (W) {
            xe(e, e.return, W);
          }
          try {
            xr(5, e, e.return);
          } catch (W) {
            xe(e, e.return, W);
          }
        }
        break;
      case 1:
        yn(n, e), zn(e), r & 512 && t !== null && It(t, t.return);
        break;
      case 5:
        if (yn(n, e), zn(e), r & 512 && t !== null && It(t, t.return), e.flags & 32) {
          var l = e.stateNode;
          try {
            Ht(l, "");
          } catch (W) {
            xe(e, e.return, W);
          }
        }
        if (r & 4 && (l = e.stateNode, l != null)) {
          var i = e.memoizedProps, o = t !== null ? t.memoizedProps : i, d = e.type, f = e.updateQueue;
          if (e.updateQueue = null, f !== null) try {
            d === "input" && i.type === "radio" && i.name != null && Qo(l, i), Gl(d, o);
            var g = Gl(d, i);
            for (o = 0; o < f.length; o += 2) {
              var N = f[o], z = f[o + 1];
              N === "style" ? ts(l, z) : N === "dangerouslySetInnerHTML" ? es(l, z) : N === "children" ? Ht(l, z) : Ne(l, N, z, g);
            }
            switch (d) {
              case "input":
                Xl(l, i);
                break;
              case "textarea":
                _o(l, i);
                break;
              case "select":
                var j = l._wrapperState.wasMultiple;
                l._wrapperState.wasMultiple = !!i.multiple;
                var O = i.value;
                O != null ? ht(l, !!i.multiple, O, !1) : j !== !!i.multiple && (i.defaultValue != null ? ht(
                  l,
                  !!i.multiple,
                  i.defaultValue,
                  !0
                ) : ht(l, !!i.multiple, i.multiple ? [] : "", !1));
            }
            l[ur] = i;
          } catch (W) {
            xe(e, e.return, W);
          }
        }
        break;
      case 6:
        if (yn(n, e), zn(e), r & 4) {
          if (e.stateNode === null) throw Error(c(162));
          l = e.stateNode, i = e.memoizedProps;
          try {
            l.nodeValue = i;
          } catch (W) {
            xe(e, e.return, W);
          }
        }
        break;
      case 3:
        if (yn(n, e), zn(e), r & 4 && t !== null && t.memoizedState.isDehydrated) try {
          _t(n.containerInfo);
        } catch (W) {
          xe(e, e.return, W);
        }
        break;
      case 4:
        yn(n, e), zn(e);
        break;
      case 13:
        yn(n, e), zn(e), l = e.child, l.flags & 8192 && (i = l.memoizedState !== null, l.stateNode.isHidden = i, !i || l.alternate !== null && l.alternate.memoizedState !== null || (So = we())), r & 4 && xa(e);
        break;
      case 22:
        if (N = t !== null && t.memoizedState !== null, e.mode & 1 ? (qe = (g = qe) || N, yn(n, e), qe = g) : yn(n, e), zn(e), r & 8192) {
          if (g = e.memoizedState !== null, (e.stateNode.isHidden = g) && !N && (e.mode & 1) !== 0) for (M = e, N = e.child; N !== null; ) {
            for (z = M = N; M !== null; ) {
              switch (j = M, O = j.child, j.tag) {
                case 0:
                case 11:
                case 14:
                case 15:
                  xr(4, j, j.return);
                  break;
                case 1:
                  It(j, j.return);
                  var I = j.stateNode;
                  if (typeof I.componentWillUnmount == "function") {
                    r = j, t = j.return;
                    try {
                      n = r, I.props = n.memoizedProps, I.state = n.memoizedState, I.componentWillUnmount();
                    } catch (W) {
                      xe(r, t, W);
                    }
                  }
                  break;
                case 5:
                  It(j, j.return);
                  break;
                case 22:
                  if (j.memoizedState !== null) {
                    ja(z);
                    continue;
                  }
              }
              O !== null ? (O.return = j, M = O) : ja(z);
            }
            N = N.sibling;
          }
          e: for (N = null, z = e; ; ) {
            if (z.tag === 5) {
              if (N === null) {
                N = z;
                try {
                  l = z.stateNode, g ? (i = l.style, typeof i.setProperty == "function" ? i.setProperty("display", "none", "important") : i.display = "none") : (d = z.stateNode, f = z.memoizedProps.style, o = f != null && f.hasOwnProperty("display") ? f.display : null, d.style.display = ns("display", o));
                } catch (W) {
                  xe(e, e.return, W);
                }
              }
            } else if (z.tag === 6) {
              if (N === null) try {
                z.stateNode.nodeValue = g ? "" : z.memoizedProps;
              } catch (W) {
                xe(e, e.return, W);
              }
            } else if ((z.tag !== 22 && z.tag !== 23 || z.memoizedState === null || z === e) && z.child !== null) {
              z.child.return = z, z = z.child;
              continue;
            }
            if (z === e) break e;
            for (; z.sibling === null; ) {
              if (z.return === null || z.return === e) break e;
              N === z && (N = null), z = z.return;
            }
            N === z && (N = null), z.sibling.return = z.return, z = z.sibling;
          }
        }
        break;
      case 19:
        yn(n, e), zn(e), r & 4 && xa(e);
        break;
      case 21:
        break;
      default:
        yn(
          n,
          e
        ), zn(e);
    }
  }
  function zn(e) {
    var n = e.flags;
    if (n & 2) {
      try {
        e: {
          for (var t = e.return; t !== null; ) {
            if (va(t)) {
              var r = t;
              break e;
            }
            t = t.return;
          }
          throw Error(c(160));
        }
        switch (r.tag) {
          case 5:
            var l = r.stateNode;
            r.flags & 32 && (Ht(l, ""), r.flags &= -33);
            var i = ga(e);
            xo(e, i, l);
            break;
          case 3:
          case 4:
            var o = r.stateNode.containerInfo, d = ga(e);
            yo(e, d, o);
            break;
          default:
            throw Error(c(161));
        }
      } catch (f) {
        xe(e, e.return, f);
      }
      e.flags &= -3;
    }
    n & 4096 && (e.flags &= -4097);
  }
  function Bd(e, n, t) {
    M = e, ka(e);
  }
  function ka(e, n, t) {
    for (var r = (e.mode & 1) !== 0; M !== null; ) {
      var l = M, i = l.child;
      if (l.tag === 22 && r) {
        var o = l.memoizedState !== null || wl;
        if (!o) {
          var d = l.alternate, f = d !== null && d.memoizedState !== null || qe;
          d = wl;
          var g = qe;
          if (wl = o, (qe = f) && !g) for (M = l; M !== null; ) o = M, f = o.child, o.tag === 22 && o.memoizedState !== null ? Ea(l) : f !== null ? (f.return = o, M = f) : Ea(l);
          for (; i !== null; ) M = i, ka(i), i = i.sibling;
          M = l, wl = d, qe = g;
        }
        Sa(e);
      } else (l.subtreeFlags & 8772) !== 0 && i !== null ? (i.return = l, M = i) : Sa(e);
    }
  }
  function Sa(e) {
    for (; M !== null; ) {
      var n = M;
      if ((n.flags & 8772) !== 0) {
        var t = n.alternate;
        try {
          if ((n.flags & 8772) !== 0) switch (n.tag) {
            case 0:
            case 11:
            case 15:
              qe || kl(5, n);
              break;
            case 1:
              var r = n.stateNode;
              if (n.flags & 4 && !qe) if (t === null) r.componentDidMount();
              else {
                var l = n.elementType === n.type ? t.memoizedProps : vn(n.type, t.memoizedProps);
                r.componentDidUpdate(l, t.memoizedState, r.__reactInternalSnapshotBeforeUpdate);
              }
              var i = n.updateQueue;
              i !== null && ju(n, i, r);
              break;
            case 3:
              var o = n.updateQueue;
              if (o !== null) {
                if (t = null, n.child !== null) switch (n.child.tag) {
                  case 5:
                    t = n.child.stateNode;
                    break;
                  case 1:
                    t = n.child.stateNode;
                }
                ju(n, o, t);
              }
              break;
            case 5:
              var d = n.stateNode;
              if (t === null && n.flags & 4) {
                t = d;
                var f = n.memoizedProps;
                switch (n.type) {
                  case "button":
                  case "input":
                  case "select":
                  case "textarea":
                    f.autoFocus && t.focus();
                    break;
                  case "img":
                    f.src && (t.src = f.src);
                }
              }
              break;
            case 6:
              break;
            case 4:
              break;
            case 12:
              break;
            case 13:
              if (n.memoizedState === null) {
                var g = n.alternate;
                if (g !== null) {
                  var N = g.memoizedState;
                  if (N !== null) {
                    var z = N.dehydrated;
                    z !== null && _t(z);
                  }
                }
              }
              break;
            case 19:
            case 17:
            case 21:
            case 22:
            case 23:
            case 25:
              break;
            default:
              throw Error(c(163));
          }
          qe || n.flags & 512 && go(n);
        } catch (j) {
          xe(n, n.return, j);
        }
      }
      if (n === e) {
        M = null;
        break;
      }
      if (t = n.sibling, t !== null) {
        t.return = n.return, M = t;
        break;
      }
      M = n.return;
    }
  }
  function ja(e) {
    for (; M !== null; ) {
      var n = M;
      if (n === e) {
        M = null;
        break;
      }
      var t = n.sibling;
      if (t !== null) {
        t.return = n.return, M = t;
        break;
      }
      M = n.return;
    }
  }
  function Ea(e) {
    for (; M !== null; ) {
      var n = M;
      try {
        switch (n.tag) {
          case 0:
          case 11:
          case 15:
            var t = n.return;
            try {
              kl(4, n);
            } catch (f) {
              xe(n, t, f);
            }
            break;
          case 1:
            var r = n.stateNode;
            if (typeof r.componentDidMount == "function") {
              var l = n.return;
              try {
                r.componentDidMount();
              } catch (f) {
                xe(n, l, f);
              }
            }
            var i = n.return;
            try {
              go(n);
            } catch (f) {
              xe(n, i, f);
            }
            break;
          case 5:
            var o = n.return;
            try {
              go(n);
            } catch (f) {
              xe(n, o, f);
            }
        }
      } catch (f) {
        xe(n, n.return, f);
      }
      if (n === e) {
        M = null;
        break;
      }
      var d = n.sibling;
      if (d !== null) {
        d.return = n.return, M = d;
        break;
      }
      M = n.return;
    }
  }
  var Xd = Math.ceil, Sl = de.ReactCurrentDispatcher, wo = de.ReactCurrentOwner, dn = de.ReactCurrentBatchConfig, Y = 0, Te = null, je = null, Me = 0, ln = 0, Wt = An(0), Re = 0, wr = null, ut = 0, jl = 0, ko = 0, kr = null, Ge = null, So = 0, Dt = 1 / 0, Mn = null, El = !1, jo = null, Qn = null, Nl = !1, Gn = null, zl = 0, Sr = 0, Eo = null, Cl = -1, Rl = 0;
  function Xe() {
    return (Y & 6) !== 0 ? we() : Cl !== -1 ? Cl : Cl = we();
  }
  function Yn(e) {
    return (e.mode & 1) === 0 ? 1 : (Y & 2) !== 0 && Me !== 0 ? Me & -Me : Cd.transition !== null ? (Rl === 0 && (Rl = gs()), Rl) : (e = te, e !== 0 || (e = window.event, e = e === void 0 ? 16 : zs(e.type)), e);
  }
  function xn(e, n, t, r) {
    if (50 < Sr) throw Sr = 0, Eo = null, Error(c(185));
    Jt(e, t, r), ((Y & 2) === 0 || e !== Te) && (e === Te && ((Y & 2) === 0 && (jl |= t), Re === 4 && _n(e, Me)), Ye(e, r), t === 1 && Y === 0 && (n.mode & 1) === 0 && (Dt = we() + 500, tl && Xn()));
  }
  function Ye(e, n) {
    var t = e.callbackNode;
    Cc(e, n);
    var r = Dr(e, e === Te ? Me : 0);
    if (r === 0) t !== null && hs(t), e.callbackNode = null, e.callbackPriority = 0;
    else if (n = r & -r, e.callbackPriority !== n) {
      if (t != null && hs(t), n === 1) e.tag === 0 ? zd(za.bind(null, e)) : du(za.bind(null, e)), Sd(function() {
        (Y & 6) === 0 && Xn();
      }), t = null;
      else {
        switch (ys(r)) {
          case 1:
            t = ti;
            break;
          case 4:
            t = ms;
            break;
          case 16:
            t = Fr;
            break;
          case 536870912:
            t = vs;
            break;
          default:
            t = Fr;
        }
        t = Ma(t, Na.bind(null, e));
      }
      e.callbackPriority = n, e.callbackNode = t;
    }
  }
  function Na(e, n) {
    if (Cl = -1, Rl = 0, (Y & 6) !== 0) throw Error(c(327));
    var t = e.callbackNode;
    if (Vt() && e.callbackNode !== t) return null;
    var r = Dr(e, e === Te ? Me : 0);
    if (r === 0) return null;
    if ((r & 30) !== 0 || (r & e.expiredLanes) !== 0 || n) n = Pl(e, r);
    else {
      n = r;
      var l = Y;
      Y |= 2;
      var i = Ra();
      (Te !== e || Me !== n) && (Mn = null, Dt = we() + 500, ct(e, n));
      do
        try {
          Kd();
          break;
        } catch (d) {
          Ca(e, d);
        }
      while (!0);
      qi(), Sl.current = i, Y = l, je !== null ? n = 0 : (Te = null, Me = 0, n = Re);
    }
    if (n !== 0) {
      if (n === 2 && (l = ri(e), l !== 0 && (r = l, n = No(e, l))), n === 1) throw t = wr, ct(e, 0), _n(e, r), Ye(e, we()), t;
      if (n === 6) _n(e, r);
      else {
        if (l = e.current.alternate, (r & 30) === 0 && !Zd(l) && (n = Pl(e, r), n === 2 && (i = ri(e), i !== 0 && (r = i, n = No(e, i))), n === 1)) throw t = wr, ct(e, 0), _n(e, r), Ye(e, we()), t;
        switch (e.finishedWork = l, e.finishedLanes = r, n) {
          case 0:
          case 1:
            throw Error(c(345));
          case 2:
            dt(e, Ge, Mn);
            break;
          case 3:
            if (_n(e, r), (r & 130023424) === r && (n = So + 500 - we(), 10 < n)) {
              if (Dr(e, 0) !== 0) break;
              if (l = e.suspendedLanes, (l & r) !== r) {
                Xe(), e.pingedLanes |= e.suspendedLanes & l;
                break;
              }
              e.timeoutHandle = Ti(dt.bind(null, e, Ge, Mn), n);
              break;
            }
            dt(e, Ge, Mn);
            break;
          case 4:
            if (_n(e, r), (r & 4194240) === r) break;
            for (n = e.eventTimes, l = -1; 0 < r; ) {
              var o = 31 - pn(r);
              i = 1 << o, o = n[o], o > l && (l = o), r &= ~i;
            }
            if (r = l, r = we() - r, r = (120 > r ? 120 : 480 > r ? 480 : 1080 > r ? 1080 : 1920 > r ? 1920 : 3e3 > r ? 3e3 : 4320 > r ? 4320 : 1960 * Xd(r / 1960)) - r, 10 < r) {
              e.timeoutHandle = Ti(dt.bind(null, e, Ge, Mn), r);
              break;
            }
            dt(e, Ge, Mn);
            break;
          case 5:
            dt(e, Ge, Mn);
            break;
          default:
            throw Error(c(329));
        }
      }
    }
    return Ye(e, we()), e.callbackNode === t ? Na.bind(null, e) : null;
  }
  function No(e, n) {
    var t = kr;
    return e.current.memoizedState.isDehydrated && (ct(e, n).flags |= 256), e = Pl(e, n), e !== 2 && (n = Ge, Ge = t, n !== null && zo(n)), e;
  }
  function zo(e) {
    Ge === null ? Ge = e : Ge.push.apply(Ge, e);
  }
  function Zd(e) {
    for (var n = e; ; ) {
      if (n.flags & 16384) {
        var t = n.updateQueue;
        if (t !== null && (t = t.stores, t !== null)) for (var r = 0; r < t.length; r++) {
          var l = t[r], i = l.getSnapshot;
          l = l.value;
          try {
            if (!hn(i(), l)) return !1;
          } catch {
            return !1;
          }
        }
      }
      if (t = n.child, n.subtreeFlags & 16384 && t !== null) t.return = n, n = t;
      else {
        if (n === e) break;
        for (; n.sibling === null; ) {
          if (n.return === null || n.return === e) return !0;
          n = n.return;
        }
        n.sibling.return = n.return, n = n.sibling;
      }
    }
    return !0;
  }
  function _n(e, n) {
    for (n &= ~ko, n &= ~jl, e.suspendedLanes |= n, e.pingedLanes &= ~n, e = e.expirationTimes; 0 < n; ) {
      var t = 31 - pn(n), r = 1 << t;
      e[t] = -1, n &= ~r;
    }
  }
  function za(e) {
    if ((Y & 6) !== 0) throw Error(c(327));
    Vt();
    var n = Dr(e, 0);
    if ((n & 1) === 0) return Ye(e, we()), null;
    var t = Pl(e, n);
    if (e.tag !== 0 && t === 2) {
      var r = ri(e);
      r !== 0 && (n = r, t = No(e, r));
    }
    if (t === 1) throw t = wr, ct(e, 0), _n(e, n), Ye(e, we()), t;
    if (t === 6) throw Error(c(345));
    return e.finishedWork = e.current.alternate, e.finishedLanes = n, dt(e, Ge, Mn), Ye(e, we()), null;
  }
  function Co(e, n) {
    var t = Y;
    Y |= 1;
    try {
      return e(n);
    } finally {
      Y = t, Y === 0 && (Dt = we() + 500, tl && Xn());
    }
  }
  function at(e) {
    Gn !== null && Gn.tag === 0 && (Y & 6) === 0 && Vt();
    var n = Y;
    Y |= 1;
    var t = dn.transition, r = te;
    try {
      if (dn.transition = null, te = 1, e) return e();
    } finally {
      te = r, dn.transition = t, Y = n, (Y & 6) === 0 && Xn();
    }
  }
  function Ro() {
    ln = Wt.current, ae(Wt);
  }
  function ct(e, n) {
    e.finishedWork = null, e.finishedLanes = 0;
    var t = e.timeoutHandle;
    if (t !== -1 && (e.timeoutHandle = -1, kd(t)), je !== null) for (t = je.return; t !== null; ) {
      var r = t;
      switch (Wi(r), r.tag) {
        case 1:
          r = r.type.childContextTypes, r != null && el();
          break;
        case 3:
          Ft(), ae(Je), ae(Ve), Gi();
          break;
        case 5:
          Ki(r);
          break;
        case 4:
          Ft();
          break;
        case 13:
          ae(me);
          break;
        case 19:
          ae(me);
          break;
        case 10:
          Ai(r.type._context);
          break;
        case 22:
        case 23:
          Ro();
      }
      t = t.return;
    }
    if (Te = e, je = e = bn(e.current, null), Me = ln = n, Re = 0, wr = null, ko = jl = ut = 0, Ge = kr = null, it !== null) {
      for (n = 0; n < it.length; n++) if (t = it[n], r = t.interleaved, r !== null) {
        t.interleaved = null;
        var l = r.next, i = t.pending;
        if (i !== null) {
          var o = i.next;
          i.next = l, r.next = o;
        }
        t.pending = r;
      }
      it = null;
    }
    return e;
  }
  function Ca(e, n) {
    do {
      var t = je;
      try {
        if (qi(), fl.current = vl, pl) {
          for (var r = ve.memoizedState; r !== null; ) {
            var l = r.queue;
            l !== null && (l.pending = null), r = r.next;
          }
          pl = !1;
        }
        if (st = 0, Pe = Ce = ve = null, hr = !1, mr = 0, wo.current = null, t === null || t.return === null) {
          Re = 1, wr = n, je = null;
          break;
        }
        e: {
          var i = e, o = t.return, d = t, f = n;
          if (n = Me, d.flags |= 32768, f !== null && typeof f == "object" && typeof f.then == "function") {
            var g = f, N = d, z = N.tag;
            if ((N.mode & 1) === 0 && (z === 0 || z === 11 || z === 15)) {
              var j = N.alternate;
              j ? (N.updateQueue = j.updateQueue, N.memoizedState = j.memoizedState, N.lanes = j.lanes) : (N.updateQueue = null, N.memoizedState = null);
            }
            var O = bu(o);
            if (O !== null) {
              O.flags &= -257, $u(O, o, d, i, n), O.mode & 1 && _u(i, g, n), n = O, f = g;
              var I = n.updateQueue;
              if (I === null) {
                var W = /* @__PURE__ */ new Set();
                W.add(f), n.updateQueue = W;
              } else I.add(f);
              break e;
            } else {
              if ((n & 1) === 0) {
                _u(i, g, n), Po();
                break e;
              }
              f = Error(c(426));
            }
          } else if (he && d.mode & 1) {
            var ke = bu(o);
            if (ke !== null) {
              (ke.flags & 65536) === 0 && (ke.flags |= 256), $u(ke, o, d, i, n), Ui(Mt(f, d));
              break e;
            }
          }
          i = f = Mt(f, d), Re !== 4 && (Re = 2), kr === null ? kr = [i] : kr.push(i), i = o;
          do {
            switch (i.tag) {
              case 3:
                i.flags |= 65536, n &= -n, i.lanes |= n;
                var m = Gu(i, f, n);
                Su(i, m);
                break e;
              case 1:
                d = f;
                var p = i.type, v = i.stateNode;
                if ((i.flags & 128) === 0 && (typeof p.getDerivedStateFromError == "function" || v !== null && typeof v.componentDidCatch == "function" && (Qn === null || !Qn.has(v)))) {
                  i.flags |= 65536, n &= -n, i.lanes |= n;
                  var C = Yu(i, d, n);
                  Su(i, C);
                  break e;
                }
            }
            i = i.return;
          } while (i !== null);
        }
        Ta(t);
      } catch (D) {
        n = D, je === t && t !== null && (je = t = t.return);
        continue;
      }
      break;
    } while (!0);
  }
  function Ra() {
    var e = Sl.current;
    return Sl.current = vl, e === null ? vl : e;
  }
  function Po() {
    (Re === 0 || Re === 3 || Re === 2) && (Re = 4), Te === null || (ut & 268435455) === 0 && (jl & 268435455) === 0 || _n(Te, Me);
  }
  function Pl(e, n) {
    var t = Y;
    Y |= 2;
    var r = Ra();
    (Te !== e || Me !== n) && (Mn = null, ct(e, n));
    do
      try {
        Jd();
        break;
      } catch (l) {
        Ca(e, l);
      }
    while (!0);
    if (qi(), Y = t, Sl.current = r, je !== null) throw Error(c(261));
    return Te = null, Me = 0, Re;
  }
  function Jd() {
    for (; je !== null; ) Pa(je);
  }
  function Kd() {
    for (; je !== null && !yc(); ) Pa(je);
  }
  function Pa(e) {
    var n = Fa(e.alternate, e, ln);
    e.memoizedProps = e.pendingProps, n === null ? Ta(e) : je = n, wo.current = null;
  }
  function Ta(e) {
    var n = e;
    do {
      var t = n.alternate;
      if (e = n.return, (n.flags & 32768) === 0) {
        if (t = Ud(t, n, ln), t !== null) {
          je = t;
          return;
        }
      } else {
        if (t = Hd(t, n), t !== null) {
          t.flags &= 32767, je = t;
          return;
        }
        if (e !== null) e.flags |= 32768, e.subtreeFlags = 0, e.deletions = null;
        else {
          Re = 6, je = null;
          return;
        }
      }
      if (n = n.sibling, n !== null) {
        je = n;
        return;
      }
      je = n = e;
    } while (n !== null);
    Re === 0 && (Re = 5);
  }
  function dt(e, n, t) {
    var r = te, l = dn.transition;
    try {
      dn.transition = null, te = 1, Qd(e, n, t, r);
    } finally {
      dn.transition = l, te = r;
    }
    return null;
  }
  function Qd(e, n, t, r) {
    do
      Vt();
    while (Gn !== null);
    if ((Y & 6) !== 0) throw Error(c(327));
    t = e.finishedWork;
    var l = e.finishedLanes;
    if (t === null) return null;
    if (e.finishedWork = null, e.finishedLanes = 0, t === e.current) throw Error(c(177));
    e.callbackNode = null, e.callbackPriority = 0;
    var i = t.lanes | t.childLanes;
    if (Rc(e, i), e === Te && (je = Te = null, Me = 0), (t.subtreeFlags & 2064) === 0 && (t.flags & 2064) === 0 || Nl || (Nl = !0, Ma(Fr, function() {
      return Vt(), null;
    })), i = (t.flags & 15990) !== 0, (t.subtreeFlags & 15990) !== 0 || i) {
      i = dn.transition, dn.transition = null;
      var o = te;
      te = 1;
      var d = Y;
      Y |= 4, wo.current = null, Ad(e, t), wa(t, e), hd(Ri), Hr = !!Ci, Ri = Ci = null, e.current = t, Bd(t), xc(), Y = d, te = o, dn.transition = i;
    } else e.current = t;
    if (Nl && (Nl = !1, Gn = e, zl = l), i = e.pendingLanes, i === 0 && (Qn = null), Sc(t.stateNode), Ye(e, we()), n !== null) for (r = e.onRecoverableError, t = 0; t < n.length; t++) l = n[t], r(l.value, { componentStack: l.stack, digest: l.digest });
    if (El) throw El = !1, e = jo, jo = null, e;
    return (zl & 1) !== 0 && e.tag !== 0 && Vt(), i = e.pendingLanes, (i & 1) !== 0 ? e === Eo ? Sr++ : (Sr = 0, Eo = e) : Sr = 0, Xn(), null;
  }
  function Vt() {
    if (Gn !== null) {
      var e = ys(zl), n = dn.transition, t = te;
      try {
        if (dn.transition = null, te = 16 > e ? 16 : e, Gn === null) var r = !1;
        else {
          if (e = Gn, Gn = null, zl = 0, (Y & 6) !== 0) throw Error(c(331));
          var l = Y;
          for (Y |= 4, M = e.current; M !== null; ) {
            var i = M, o = i.child;
            if ((M.flags & 16) !== 0) {
              var d = i.deletions;
              if (d !== null) {
                for (var f = 0; f < d.length; f++) {
                  var g = d[f];
                  for (M = g; M !== null; ) {
                    var N = M;
                    switch (N.tag) {
                      case 0:
                      case 11:
                      case 15:
                        xr(8, N, i);
                    }
                    var z = N.child;
                    if (z !== null) z.return = N, M = z;
                    else for (; M !== null; ) {
                      N = M;
                      var j = N.sibling, O = N.return;
                      if (ma(N), N === g) {
                        M = null;
                        break;
                      }
                      if (j !== null) {
                        j.return = O, M = j;
                        break;
                      }
                      M = O;
                    }
                  }
                }
                var I = i.alternate;
                if (I !== null) {
                  var W = I.child;
                  if (W !== null) {
                    I.child = null;
                    do {
                      var ke = W.sibling;
                      W.sibling = null, W = ke;
                    } while (W !== null);
                  }
                }
                M = i;
              }
            }
            if ((i.subtreeFlags & 2064) !== 0 && o !== null) o.return = i, M = o;
            else e: for (; M !== null; ) {
              if (i = M, (i.flags & 2048) !== 0) switch (i.tag) {
                case 0:
                case 11:
                case 15:
                  xr(9, i, i.return);
              }
              var m = i.sibling;
              if (m !== null) {
                m.return = i.return, M = m;
                break e;
              }
              M = i.return;
            }
          }
          var p = e.current;
          for (M = p; M !== null; ) {
            o = M;
            var v = o.child;
            if ((o.subtreeFlags & 2064) !== 0 && v !== null) v.return = o, M = v;
            else e: for (o = p; M !== null; ) {
              if (d = M, (d.flags & 2048) !== 0) try {
                switch (d.tag) {
                  case 0:
                  case 11:
                  case 15:
                    kl(9, d);
                }
              } catch (D) {
                xe(d, d.return, D);
              }
              if (d === o) {
                M = null;
                break e;
              }
              var C = d.sibling;
              if (C !== null) {
                C.return = d.return, M = C;
                break e;
              }
              M = d.return;
            }
          }
          if (Y = l, Xn(), Sn && typeof Sn.onPostCommitFiberRoot == "function") try {
            Sn.onPostCommitFiberRoot(Mr, e);
          } catch {
          }
          r = !0;
        }
        return r;
      } finally {
        te = t, dn.transition = n;
      }
    }
    return !1;
  }
  function La(e, n, t) {
    n = Mt(t, n), n = Gu(e, n, 1), e = Jn(e, n, 1), n = Xe(), e !== null && (Jt(e, 1, n), Ye(e, n));
  }
  function xe(e, n, t) {
    if (e.tag === 3) La(e, e, t);
    else for (; n !== null; ) {
      if (n.tag === 3) {
        La(n, e, t);
        break;
      } else if (n.tag === 1) {
        var r = n.stateNode;
        if (typeof n.type.getDerivedStateFromError == "function" || typeof r.componentDidCatch == "function" && (Qn === null || !Qn.has(r))) {
          e = Mt(t, e), e = Yu(n, e, 1), n = Jn(n, e, 1), e = Xe(), n !== null && (Jt(n, 1, e), Ye(n, e));
          break;
        }
      }
      n = n.return;
    }
  }
  function Gd(e, n, t) {
    var r = e.pingCache;
    r !== null && r.delete(n), n = Xe(), e.pingedLanes |= e.suspendedLanes & t, Te === e && (Me & t) === t && (Re === 4 || Re === 3 && (Me & 130023424) === Me && 500 > we() - So ? ct(e, 0) : ko |= t), Ye(e, n);
  }
  function Oa(e, n) {
    n === 0 && ((e.mode & 1) === 0 ? n = 1 : (n = Wr, Wr <<= 1, (Wr & 130023424) === 0 && (Wr = 4194304)));
    var t = Xe();
    e = Ln(e, n), e !== null && (Jt(e, n, t), Ye(e, t));
  }
  function Yd(e) {
    var n = e.memoizedState, t = 0;
    n !== null && (t = n.retryLane), Oa(e, t);
  }
  function _d(e, n) {
    var t = 0;
    switch (e.tag) {
      case 13:
        var r = e.stateNode, l = e.memoizedState;
        l !== null && (t = l.retryLane);
        break;
      case 19:
        r = e.stateNode;
        break;
      default:
        throw Error(c(314));
    }
    r !== null && r.delete(n), Oa(e, t);
  }
  var Fa;
  Fa = function(e, n, t) {
    if (e !== null) if (e.memoizedProps !== n.pendingProps || Je.current) Qe = !0;
    else {
      if ((e.lanes & t) === 0 && (n.flags & 128) === 0) return Qe = !1, Vd(e, n, t);
      Qe = (e.flags & 131072) !== 0;
    }
    else Qe = !1, he && (n.flags & 1048576) !== 0 && fu(n, ll, n.index);
    switch (n.lanes = 0, n.tag) {
      case 2:
        var r = n.type;
        xl(e, n), e = n.pendingProps;
        var l = zt(n, Ve.current);
        Ot(n, t), l = bi(null, n, r, e, l, t);
        var i = $i();
        return n.flags |= 1, typeof l == "object" && l !== null && typeof l.render == "function" && l.$$typeof === void 0 ? (n.tag = 1, n.memoizedState = null, n.updateQueue = null, Ke(r) ? (i = !0, nl(n)) : i = !1, n.memoizedState = l.state !== null && l.state !== void 0 ? l.state : null, Zi(n), l.updater = gl, n.stateNode = l, l._reactInternals = n, io(n, r, e, t), n = ao(null, n, r, !0, i, t)) : (n.tag = 0, he && i && Ii(n), Be(null, n, l, t), n = n.child), n;
      case 16:
        r = n.elementType;
        e: {
          switch (xl(e, n), e = n.pendingProps, l = r._init, r = l(r._payload), n.type = r, l = n.tag = $d(r), e = vn(r, e), l) {
            case 0:
              n = uo(null, n, r, e, t);
              break e;
            case 1:
              n = ia(null, n, r, e, t);
              break e;
            case 11:
              n = ea(null, n, r, e, t);
              break e;
            case 14:
              n = na(null, n, r, vn(r.type, e), t);
              break e;
          }
          throw Error(c(
            306,
            r,
            ""
          ));
        }
        return n;
      case 0:
        return r = n.type, l = n.pendingProps, l = n.elementType === r ? l : vn(r, l), uo(e, n, r, l, t);
      case 1:
        return r = n.type, l = n.pendingProps, l = n.elementType === r ? l : vn(r, l), ia(e, n, r, l, t);
      case 3:
        e: {
          if (oa(n), e === null) throw Error(c(387));
          r = n.pendingProps, i = n.memoizedState, l = i.element, ku(e, n), cl(n, r, null, t);
          var o = n.memoizedState;
          if (r = o.element, i.isDehydrated) if (i = { element: r, isDehydrated: !1, cache: o.cache, pendingSuspenseBoundaries: o.pendingSuspenseBoundaries, transitions: o.transitions }, n.updateQueue.baseState = i, n.memoizedState = i, n.flags & 256) {
            l = Mt(Error(c(423)), n), n = sa(e, n, r, t, l);
            break e;
          } else if (r !== l) {
            l = Mt(Error(c(424)), n), n = sa(e, n, r, t, l);
            break e;
          } else for (rn = qn(n.stateNode.containerInfo.firstChild), tn = n, he = !0, mn = null, t = xu(n, null, r, t), n.child = t; t; ) t.flags = t.flags & -3 | 4096, t = t.sibling;
          else {
            if (Pt(), r === l) {
              n = Fn(e, n, t);
              break e;
            }
            Be(e, n, r, t);
          }
          n = n.child;
        }
        return n;
      case 5:
        return Eu(n), e === null && Vi(n), r = n.type, l = n.pendingProps, i = e !== null ? e.memoizedProps : null, o = l.children, Pi(r, l) ? o = null : i !== null && Pi(r, i) && (n.flags |= 32), la(e, n), Be(e, n, o, t), n.child;
      case 6:
        return e === null && Vi(n), null;
      case 13:
        return ua(e, n, t);
      case 4:
        return Ji(n, n.stateNode.containerInfo), r = n.pendingProps, e === null ? n.child = Tt(n, null, r, t) : Be(e, n, r, t), n.child;
      case 11:
        return r = n.type, l = n.pendingProps, l = n.elementType === r ? l : vn(r, l), ea(e, n, r, l, t);
      case 7:
        return Be(e, n, n.pendingProps, t), n.child;
      case 8:
        return Be(e, n, n.pendingProps.children, t), n.child;
      case 12:
        return Be(e, n, n.pendingProps.children, t), n.child;
      case 10:
        e: {
          if (r = n.type._context, l = n.pendingProps, i = n.memoizedProps, o = l.value, ie(sl, r._currentValue), r._currentValue = o, i !== null) if (hn(i.value, o)) {
            if (i.children === l.children && !Je.current) {
              n = Fn(e, n, t);
              break e;
            }
          } else for (i = n.child, i !== null && (i.return = n); i !== null; ) {
            var d = i.dependencies;
            if (d !== null) {
              o = i.child;
              for (var f = d.firstContext; f !== null; ) {
                if (f.context === r) {
                  if (i.tag === 1) {
                    f = On(-1, t & -t), f.tag = 2;
                    var g = i.updateQueue;
                    if (g !== null) {
                      g = g.shared;
                      var N = g.pending;
                      N === null ? f.next = f : (f.next = N.next, N.next = f), g.pending = f;
                    }
                  }
                  i.lanes |= t, f = i.alternate, f !== null && (f.lanes |= t), Bi(
                    i.return,
                    t,
                    n
                  ), d.lanes |= t;
                  break;
                }
                f = f.next;
              }
            } else if (i.tag === 10) o = i.type === n.type ? null : i.child;
            else if (i.tag === 18) {
              if (o = i.return, o === null) throw Error(c(341));
              o.lanes |= t, d = o.alternate, d !== null && (d.lanes |= t), Bi(o, t, n), o = i.sibling;
            } else o = i.child;
            if (o !== null) o.return = i;
            else for (o = i; o !== null; ) {
              if (o === n) {
                o = null;
                break;
              }
              if (i = o.sibling, i !== null) {
                i.return = o.return, o = i;
                break;
              }
              o = o.return;
            }
            i = o;
          }
          Be(e, n, l.children, t), n = n.child;
        }
        return n;
      case 9:
        return l = n.type, r = n.pendingProps.children, Ot(n, t), l = an(l), r = r(l), n.flags |= 1, Be(e, n, r, t), n.child;
      case 14:
        return r = n.type, l = vn(r, n.pendingProps), l = vn(r.type, l), na(e, n, r, l, t);
      case 15:
        return ta(e, n, n.type, n.pendingProps, t);
      case 17:
        return r = n.type, l = n.pendingProps, l = n.elementType === r ? l : vn(r, l), xl(e, n), n.tag = 1, Ke(r) ? (e = !0, nl(n)) : e = !1, Ot(n, t), Ku(n, r, l), io(n, r, l, t), ao(null, n, r, !0, e, t);
      case 19:
        return ca(e, n, t);
      case 22:
        return ra(e, n, t);
    }
    throw Error(c(156, n.tag));
  };
  function Ma(e, n) {
    return ps(e, n);
  }
  function bd(e, n, t, r) {
    this.tag = e, this.key = t, this.sibling = this.child = this.return = this.stateNode = this.type = this.elementType = null, this.index = 0, this.ref = null, this.pendingProps = n, this.dependencies = this.memoizedState = this.updateQueue = this.memoizedProps = null, this.mode = r, this.subtreeFlags = this.flags = 0, this.deletions = null, this.childLanes = this.lanes = 0, this.alternate = null;
  }
  function fn(e, n, t, r) {
    return new bd(e, n, t, r);
  }
  function To(e) {
    return e = e.prototype, !(!e || !e.isReactComponent);
  }
  function $d(e) {
    if (typeof e == "function") return To(e) ? 1 : 0;
    if (e != null) {
      if (e = e.$$typeof, e === We) return 11;
      if (e === De) return 14;
    }
    return 2;
  }
  function bn(e, n) {
    var t = e.alternate;
    return t === null ? (t = fn(e.tag, n, e.key, e.mode), t.elementType = e.elementType, t.type = e.type, t.stateNode = e.stateNode, t.alternate = e, e.alternate = t) : (t.pendingProps = n, t.type = e.type, t.flags = 0, t.subtreeFlags = 0, t.deletions = null), t.flags = e.flags & 14680064, t.childLanes = e.childLanes, t.lanes = e.lanes, t.child = e.child, t.memoizedProps = e.memoizedProps, t.memoizedState = e.memoizedState, t.updateQueue = e.updateQueue, n = e.dependencies, t.dependencies = n === null ? null : { lanes: n.lanes, firstContext: n.firstContext }, t.sibling = e.sibling, t.index = e.index, t.ref = e.ref, t;
  }
  function Tl(e, n, t, r, l, i) {
    var o = 2;
    if (r = e, typeof e == "function") To(e) && (o = 1);
    else if (typeof e == "string") o = 5;
    else e: switch (e) {
      case Se:
        return ft(t.children, l, i, n);
      case ye:
        o = 8, l |= 8;
        break;
      case Ze:
        return e = fn(12, t, n, l | 2), e.elementType = Ze, e.lanes = i, e;
      case ee:
        return e = fn(13, t, n, l), e.elementType = ee, e.lanes = i, e;
      case ze:
        return e = fn(19, t, n, l), e.elementType = ze, e.lanes = i, e;
      case se:
        return Ll(t, l, i, n);
      default:
        if (typeof e == "object" && e !== null) switch (e.$$typeof) {
          case Ae:
            o = 10;
            break e;
          case $e:
            o = 9;
            break e;
          case We:
            o = 11;
            break e;
          case De:
            o = 14;
            break e;
          case Oe:
            o = 16, r = null;
            break e;
        }
        throw Error(c(130, e == null ? e : typeof e, ""));
    }
    return n = fn(o, t, n, l), n.elementType = e, n.type = r, n.lanes = i, n;
  }
  function ft(e, n, t, r) {
    return e = fn(7, e, r, n), e.lanes = t, e;
  }
  function Ll(e, n, t, r) {
    return e = fn(22, e, r, n), e.elementType = se, e.lanes = t, e.stateNode = { isHidden: !1 }, e;
  }
  function Lo(e, n, t) {
    return e = fn(6, e, null, n), e.lanes = t, e;
  }
  function Oo(e, n, t) {
    return n = fn(4, e.children !== null ? e.children : [], e.key, n), n.lanes = t, n.stateNode = { containerInfo: e.containerInfo, pendingChildren: null, implementation: e.implementation }, n;
  }
  function ef(e, n, t, r, l) {
    this.tag = n, this.containerInfo = e, this.finishedWork = this.pingCache = this.current = this.pendingChildren = null, this.timeoutHandle = -1, this.callbackNode = this.pendingContext = this.context = null, this.callbackPriority = 0, this.eventTimes = li(0), this.expirationTimes = li(-1), this.entangledLanes = this.finishedLanes = this.mutableReadLanes = this.expiredLanes = this.pingedLanes = this.suspendedLanes = this.pendingLanes = 0, this.entanglements = li(0), this.identifierPrefix = r, this.onRecoverableError = l, this.mutableSourceEagerHydrationData = null;
  }
  function Fo(e, n, t, r, l, i, o, d, f) {
    return e = new ef(e, n, t, d, f), n === 1 ? (n = 1, i === !0 && (n |= 8)) : n = 0, i = fn(3, null, null, n), e.current = i, i.stateNode = e, i.memoizedState = { element: r, isDehydrated: t, cache: null, transitions: null, pendingSuspenseBoundaries: null }, Zi(i), e;
  }
  function nf(e, n, t) {
    var r = 3 < arguments.length && arguments[3] !== void 0 ? arguments[3] : null;
    return { $$typeof: fe, key: r == null ? null : "" + r, children: e, containerInfo: n, implementation: t };
  }
  function Ia(e) {
    if (!e) return Bn;
    e = e._reactInternals;
    e: {
      if (et(e) !== e || e.tag !== 1) throw Error(c(170));
      var n = e;
      do {
        switch (n.tag) {
          case 3:
            n = n.stateNode.context;
            break e;
          case 1:
            if (Ke(n.type)) {
              n = n.stateNode.__reactInternalMemoizedMergedChildContext;
              break e;
            }
        }
        n = n.return;
      } while (n !== null);
      throw Error(c(171));
    }
    if (e.tag === 1) {
      var t = e.type;
      if (Ke(t)) return au(e, t, n);
    }
    return n;
  }
  function Wa(e, n, t, r, l, i, o, d, f) {
    return e = Fo(t, r, !0, e, l, i, o, d, f), e.context = Ia(null), t = e.current, r = Xe(), l = Yn(t), i = On(r, l), i.callback = n ?? null, Jn(t, i, l), e.current.lanes = l, Jt(e, l, r), Ye(e, r), e;
  }
  function Ol(e, n, t, r) {
    var l = n.current, i = Xe(), o = Yn(l);
    return t = Ia(t), n.context === null ? n.context = t : n.pendingContext = t, n = On(i, o), n.payload = { element: e }, r = r === void 0 ? null : r, r !== null && (n.callback = r), e = Jn(l, n, o), e !== null && (xn(e, l, o, i), al(e, l, o)), o;
  }
  function Fl(e) {
    if (e = e.current, !e.child) return null;
    switch (e.child.tag) {
      case 5:
        return e.child.stateNode;
      default:
        return e.child.stateNode;
    }
  }
  function Da(e, n) {
    if (e = e.memoizedState, e !== null && e.dehydrated !== null) {
      var t = e.retryLane;
      e.retryLane = t !== 0 && t < n ? t : n;
    }
  }
  function Mo(e, n) {
    Da(e, n), (e = e.alternate) && Da(e, n);
  }
  function tf() {
    return null;
  }
  var Va = typeof reportError == "function" ? reportError : function(e) {
    console.error(e);
  };
  function Io(e) {
    this._internalRoot = e;
  }
  Ml.prototype.render = Io.prototype.render = function(e) {
    var n = this._internalRoot;
    if (n === null) throw Error(c(409));
    Ol(e, n, null, null);
  }, Ml.prototype.unmount = Io.prototype.unmount = function() {
    var e = this._internalRoot;
    if (e !== null) {
      this._internalRoot = null;
      var n = e.containerInfo;
      at(function() {
        Ol(null, e, null, null);
      }), n[Cn] = null;
    }
  };
  function Ml(e) {
    this._internalRoot = e;
  }
  Ml.prototype.unstable_scheduleHydration = function(e) {
    if (e) {
      var n = ks();
      e = { blockedOn: null, target: e, priority: n };
      for (var t = 0; t < Vn.length && n !== 0 && n < Vn[t].priority; t++) ;
      Vn.splice(t, 0, e), t === 0 && Es(e);
    }
  };
  function Wo(e) {
    return !(!e || e.nodeType !== 1 && e.nodeType !== 9 && e.nodeType !== 11);
  }
  function Il(e) {
    return !(!e || e.nodeType !== 1 && e.nodeType !== 9 && e.nodeType !== 11 && (e.nodeType !== 8 || e.nodeValue !== " react-mount-point-unstable "));
  }
  function Ua() {
  }
  function rf(e, n, t, r, l) {
    if (l) {
      if (typeof r == "function") {
        var i = r;
        r = function() {
          var g = Fl(o);
          i.call(g);
        };
      }
      var o = Wa(n, r, e, 0, null, !1, !1, "", Ua);
      return e._reactRootContainer = o, e[Cn] = o.current, or(e.nodeType === 8 ? e.parentNode : e), at(), o;
    }
    for (; l = e.lastChild; ) e.removeChild(l);
    if (typeof r == "function") {
      var d = r;
      r = function() {
        var g = Fl(f);
        d.call(g);
      };
    }
    var f = Fo(e, 0, !1, null, null, !1, !1, "", Ua);
    return e._reactRootContainer = f, e[Cn] = f.current, or(e.nodeType === 8 ? e.parentNode : e), at(function() {
      Ol(n, f, t, r);
    }), f;
  }
  function Wl(e, n, t, r, l) {
    var i = t._reactRootContainer;
    if (i) {
      var o = i;
      if (typeof l == "function") {
        var d = l;
        l = function() {
          var f = Fl(o);
          d.call(f);
        };
      }
      Ol(n, o, e, l);
    } else o = rf(t, n, e, l, r);
    return Fl(o);
  }
  xs = function(e) {
    switch (e.tag) {
      case 3:
        var n = e.stateNode;
        if (n.current.memoizedState.isDehydrated) {
          var t = Zt(n.pendingLanes);
          t !== 0 && (ii(n, t | 1), Ye(n, we()), (Y & 6) === 0 && (Dt = we() + 500, Xn()));
        }
        break;
      case 13:
        at(function() {
          var r = Ln(e, 1);
          if (r !== null) {
            var l = Xe();
            xn(r, e, 1, l);
          }
        }), Mo(e, 1);
    }
  }, oi = function(e) {
    if (e.tag === 13) {
      var n = Ln(e, 134217728);
      if (n !== null) {
        var t = Xe();
        xn(n, e, 134217728, t);
      }
      Mo(e, 134217728);
    }
  }, ws = function(e) {
    if (e.tag === 13) {
      var n = Yn(e), t = Ln(e, n);
      if (t !== null) {
        var r = Xe();
        xn(t, e, n, r);
      }
      Mo(e, n);
    }
  }, ks = function() {
    return te;
  }, Ss = function(e, n) {
    var t = te;
    try {
      return te = e, n();
    } finally {
      te = t;
    }
  }, bl = function(e, n, t) {
    switch (n) {
      case "input":
        if (Xl(e, t), n = t.name, t.type === "radio" && n != null) {
          for (t = e; t.parentNode; ) t = t.parentNode;
          for (t = t.querySelectorAll("input[name=" + JSON.stringify("" + n) + '][type="radio"]'), n = 0; n < t.length; n++) {
            var r = t[n];
            if (r !== e && r.form === e.form) {
              var l = $r(r);
              if (!l) throw Error(c(90));
              Jo(r), Xl(r, l);
            }
          }
        }
        break;
      case "textarea":
        _o(e, t);
        break;
      case "select":
        n = t.value, n != null && ht(e, !!t.multiple, n, !1);
    }
  }, os = Co, ss = at;
  var lf = { usingClientEntryPoint: !1, Events: [ar, Et, $r, ls, is, Co] }, jr = { findFiberByHostInstance: nt, bundleType: 0, version: "18.3.1", rendererPackageName: "react-dom" }, of = { bundleType: jr.bundleType, version: jr.version, rendererPackageName: jr.rendererPackageName, rendererConfig: jr.rendererConfig, overrideHookState: null, overrideHookStateDeletePath: null, overrideHookStateRenamePath: null, overrideProps: null, overridePropsDeletePath: null, overridePropsRenamePath: null, setErrorHandler: null, setSuspenseHandler: null, scheduleUpdate: null, currentDispatcherRef: de.ReactCurrentDispatcher, findHostInstanceByFiber: function(e) {
    return e = ds(e), e === null ? null : e.stateNode;
  }, findFiberByHostInstance: jr.findFiberByHostInstance || tf, findHostInstancesForRefresh: null, scheduleRefresh: null, scheduleRoot: null, setRefreshHandler: null, getCurrentFiber: null, reconcilerVersion: "18.3.1-next-f1338f8080-20240426" };
  if (typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ < "u") {
    var Dl = __REACT_DEVTOOLS_GLOBAL_HOOK__;
    if (!Dl.isDisabled && Dl.supportsFiber) try {
      Mr = Dl.inject(of), Sn = Dl;
    } catch {
    }
  }
  return _e.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED = lf, _e.createPortal = function(e, n) {
    var t = 2 < arguments.length && arguments[2] !== void 0 ? arguments[2] : null;
    if (!Wo(n)) throw Error(c(200));
    return nf(e, n, null, t);
  }, _e.createRoot = function(e, n) {
    if (!Wo(e)) throw Error(c(299));
    var t = !1, r = "", l = Va;
    return n != null && (n.unstable_strictMode === !0 && (t = !0), n.identifierPrefix !== void 0 && (r = n.identifierPrefix), n.onRecoverableError !== void 0 && (l = n.onRecoverableError)), n = Fo(e, 1, !1, null, null, t, !1, r, l), e[Cn] = n.current, or(e.nodeType === 8 ? e.parentNode : e), new Io(n);
  }, _e.findDOMNode = function(e) {
    if (e == null) return null;
    if (e.nodeType === 1) return e;
    var n = e._reactInternals;
    if (n === void 0)
      throw typeof e.render == "function" ? Error(c(188)) : (e = Object.keys(e).join(","), Error(c(268, e)));
    return e = ds(n), e = e === null ? null : e.stateNode, e;
  }, _e.flushSync = function(e) {
    return at(e);
  }, _e.hydrate = function(e, n, t) {
    if (!Il(n)) throw Error(c(200));
    return Wl(null, e, n, !0, t);
  }, _e.hydrateRoot = function(e, n, t) {
    if (!Wo(e)) throw Error(c(405));
    var r = t != null && t.hydratedSources || null, l = !1, i = "", o = Va;
    if (t != null && (t.unstable_strictMode === !0 && (l = !0), t.identifierPrefix !== void 0 && (i = t.identifierPrefix), t.onRecoverableError !== void 0 && (o = t.onRecoverableError)), n = Wa(n, null, e, 1, t ?? null, l, !1, i, o), e[Cn] = n.current, or(e), r) for (e = 0; e < r.length; e++) t = r[e], l = t._getVersion, l = l(t._source), n.mutableSourceEagerHydrationData == null ? n.mutableSourceEagerHydrationData = [t, l] : n.mutableSourceEagerHydrationData.push(
      t,
      l
    );
    return new Ml(n);
  }, _e.render = function(e, n, t) {
    if (!Il(n)) throw Error(c(200));
    return Wl(null, e, n, !1, t);
  }, _e.unmountComponentAtNode = function(e) {
    if (!Il(e)) throw Error(c(40));
    return e._reactRootContainer ? (at(function() {
      Wl(null, null, e, !1, function() {
        e._reactRootContainer = null, e[Cn] = null;
      });
    }), !0) : !1;
  }, _e.unstable_batchedUpdates = Co, _e.unstable_renderSubtreeIntoContainer = function(e, n, t, r) {
    if (!Il(t)) throw Error(c(200));
    if (e == null || e._reactInternals === void 0) throw Error(c(38));
    return Wl(e, n, t, !1, r);
  }, _e.version = "18.3.1-next-f1338f8080-20240426", _e;
}
var Ka;
function hf() {
  if (Ka) return Uo.exports;
  Ka = 1;
  function u() {
    if (!(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ > "u" || typeof __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE != "function"))
      try {
        __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE(u);
      } catch (a) {
        console.error(a);
      }
  }
  return u(), Uo.exports = pf(), Uo.exports;
}
var Qa;
function mf() {
  if (Qa) return Vl;
  Qa = 1;
  var u = hf();
  return Vl.createRoot = u.createRoot, Vl.hydrateRoot = u.hydrateRoot, Vl;
}
var vf = mf();
const gf = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAKAAAACgCAYAAACLz2ctAABg1ElEQVR42u29d5xdV3X+/V17n3NunV7Ue7EsWW5yrxLYGEwzCTMmQEIvAUJNAiGQ0aSREELPj1BCCSVhBkwLBEyRTLEx7kWSi6xep8/cfs7Ze79/nHunyE57PwnIMFufse6MrueW89xVn/UsmD/zZ/7Mn/kzf+bP/Jk/82f+zJ/5M3/mz/yZP/Nn/syf+TN/5s/8mT+/xqevr08552T+nZg/v9TjcOJ6BvT8OzF/fvng6+tTjdul139psXvJZ1oTUDJvCX+Jx/uNBF/PgJb+XnP82r/LtZ+z4p0e/uvD1W0/wdfPJoqZx+A8AP9vwTfYa4qv/dR5QVPLP/stLWcxVYR8ep0LYxER55wTEXHz8Pi/P+o3ze3KYK+pvekz56ba2n7gtzafZeNKjcg4O1mJ5k3fvAX8P4/5iq/++CLxc9/wstl2UynHID6+ElWs6WkAzsNw3gL+r5/du0X6+61O5/7Ob21bbmqVWMAThVjlIIpX1X6xb009PZ6H4DwA/7fjvkFTfvWnLvWz2RcS14yI8kQJgogVZQKCtDx87EoAtu9U89CYB+B/egZ6nP5vF4839jgAGwRv0bmcYI0TkcTXOofyNIjDHJ14EVqAnXYeGr+c82vvahxOBHFTz3pfZ7BqwSOp9rY2ayMnSgkOnHOIEkwUO4c4zlt6ZdBz0a1uYEBLb6+Zh8i8BXwcoAC++bL9z7jz41Ods3/2hKdnUAHUsvqKVDrXZq2xoAQREEFU8hYo37e+8pXdc/xvnXMyOAjz7bl5AD7O7QrivvqiR7cvalr5nbhWejnAzr6d/3E7bWhXAqIwvhDlOSViRQBXt/9KQClEiTaeMynnX1F+33f+unew17Bzp54H4TwA6+Ab0L2DYv7lxj1bc+ncn02Vx2zxRO3Z4sO2/q3/savcigWwTjZhjJAEf/UARGaCEAFRomIXmWzRvOPwp3a8SrZti9mO9Dk3n5T8pgOwZ7DH7rh6hxd43vuzqYxEtkw8pS8+9MPC2a4O0P/s/4+MySK24cdngDer3+FExLNOHVuSN9+7etEnPvbYru3SL7ZfxPbt2OHNW8PfUAA2XO/JxUue25JtPy+2VeOlPJuzTf7hn069Vviv22YmioyrhiBSx5zMgE8EJ4ICTDaQ+69aoiSvncpk+z6yb/e3P31477r+bdtiEXEDzum6RZwH4//CeVJ0QnZtTKCihVcFWrs4sVc6NFUnQ7zo2F3lv128JXPI9Tkl/fKEJRTRqhhNlQg68oiSWTWAJBkBkNgysjLPVHtK2kJDDWNq+fz1U8XC5R9+9IF/TDv70V6RI43f2bdjh7dpeNj19PTY+d7xrykA68QA+8/P29sN8aWhrQjKKYWI09akbFPz3q+Pb0eyL9u502lgLgB3opKfyaOmEhKFkfMCb1bgV3fDCrCOsfY0VgtaFDktOhsbk0plWsJU8PaJyYlXfmDvA1/yjfli932P3Nm7bVs8baUHBvSuri5h607bL/3zdcRfFwAO9iaeEa96vq/zzc5Zq+u1E0HpWlSy/lTmpXe9/+S3trxFbtrRt8Pb1j8DjJ2NG9btKpcqeGOT0rK0GxsbZNoNu+RvB3HgoURQAsaBUqKbUc5Gsc1k8x1Ryv+DicnJPzh23oYHPvjo/d9Ji/5+zvp39K5fPzX7Q7N9507N1q22X2QejE9mAHYN7ZT6RV2d9jMgxrqkeJJ4ThGcsa50QD5+z8f2333e76864Aacll4xAFu3YrkFYqfvnAorxj8+qvML21GicM4mSbEDZxM7GdQSYE5XaZLbopToJsRJbE02nfGs72+OtN48VSq9fbJWO/TR/btvw7qbfc+/RUQeA+IGGAdB9YJl3k0/OWNAgCiKWq1xKG0RNFL/AyhjQ5tS2c7J3fZr3//rI9dIr4zu6HPetn6Jpb/fOpzQPLh3f2HvPV5ot0wdG7FtyxdpF0Yk+YsgokA72kaqaJugT8lscozU2dLOy2oP7bAuNjbv+SoMguU1Ty2vxObGcqlU/shju+8MFF9XofmuiOwBDMCAc3oeiE+yLHi4e6sDiGy8yjgzE7s5B9YhDpTSKrQVk9G5c73j/r//4i9Gl23rl3i6X9wzqGSw10hKfcDTWiYPnKA2VURpBdaBc4i1OF/TcaxIfrRC7KmZGk3dJSuZgX3dCntZz1Otom23wSxyYhamM9n2pvxVQT7//tBT9/7j/l03f+LAnhd96DvfSfWKGOqZ9Dz0nmR1QIOpRdZgrMHaU+rOLokHK3HRZHTmwtoIt9367uFn9w6KERG3c2OPDPQM6JUL2gYnw8o9aefp4YcPGhPV82ljwVosFl0zrH9wDOdplAWpgy/hzUg9Pkxg2LCQDqdERGe0p7v8lFuitOmKrWlLpYJ0Nnct6fQXvA3L7/p/+/e8/O9vvTXTK2KcczJfV3wSAHBXPQYMo/hANaxhnE3is3o9zzqHqycRgtLVuGwUsoSS982fvHXoH37Wd7x7W7/EvYO9ZnD81TaU4PWhxNWoFMqJhw86B4hzOGORMMaKZcWeMZYeLFHL+Wjjpt29uCQmFBG0CKoOQq0UShRIkm470E1+oBenM24BYtK10ARBelOQy/5TdknH7R/bt6tXRJzMW8MnjwW0YTxSrJYxzmGNwTkSN9xIYl0CQoXSsYlsGNZcRvKvs+Pe3T996/Af//hPjnX1DorZ+L0/vq3kxW8LIlThxIQ7vucAFpckNMZCbKAWcu5399F1rEwtH6CdQwFKzbaGM1WchltOAJl8OCwO45yktKeX5Zv0Iu1ZSmXjlNosmcyX//HAnn/50N13d/WKmL4dO7x5AJ6mZ1P3cMLlE44UagWmikUdG0Nk4noa7HBuBouQ9HS1UlIOC8ZT3pKM5P7WFtT9O35/6H07Xrn/3I3f6ft/nNvxnbasrwrHTpqjD+wlrMUoz8MZg7UWb6LMJYN7WLVrlDiTwvoaZeuWVuZ4/ye8jci0lTbWkvY8tSSb0+dlmmxTGBuTCl6Q7sjd+pFH7r+2f9u2uGdgQPMb6JJPfxc8uCsBYDV+JDLV6lSlLMZYV63VMA1L2Cji1f8Sl1glLUpHcc0Va1PGF39hU7rpbZJK3/mDVxz94cl1L1gzccYlxOk2VRyd4vBd91E4eRLtHBJbjAKpRmz+2h7Ou+lhmsarxNkAtEJZNx0TzuY2kAQDMx2+umWU6VgRjEL91qIVeh1+HAlrdSr494/v3fXHg729po/tv3Fx4ZPixfbRp/rZ7t7zlB/sSPm5qxa0NttskNaeVuQymemLnHzVyycis8yiYJ119dqylwly1Ko1qsqiCVG1CXTpJH7xON0tMYsWBqQ8cE6I0XihxeRSHN+ymMMXLaHSEhBUoiQZb4DLNYA3t8LiXAOUiaWuGMM5TW0szzZxz9iQvWVsSNra2ySemvrwK1dtfFOfc6of3G9KqebJEQNevVWBOGfc54y1cnx8FAeExlCqVmlEYrNdYePCNz5mSilBxENwlbBkjI5cQIygiFOdVDo2U1j5NPbmtnJ78Rx2lVYzUmtGjIEghlqVJTv2s+VT97D0rhOYwMNqjdhZj4Ob65JngbJes8RTioO1MiaOOK+1U13ftYSp8YnYa2554+f2P/TBfhHbt3OnnreAp9VxAuL+9rKfNoV+4SGUv6gj3+QWtnQoYw3pVIp8Jo1WCpFTLrqAuAbvz00nLwk46rbJ2WnoOFEYJ0QGlFhyqsgCPcRi7wSZoIY1HioSxs/sYu8z11FqS6PKIU7LDPpnUb1c449LmtQOMM5xeUsnzcpDlGJPYdz9YOSEaW9r9aJC8ZUvW7nhnwac070iZt4Cnh6fEzfQ4/Tbb72i4Jx8OFAZOTYxbCfKBbTSlKtVJgolYmNmTE/dCmKTv611czNnklgx+VYBCueSwrSyhpTEeDiKUZ6HKmu4rXg+DxdXEzmFS8e0PDTEOZ+6i/Z940S5AMxM/OdcwwK76e9tY/4EMM4yFoWICFEcc2Zzm1zS2qFHp6aM872P/uD4Yxf1ipiBgV9/4aQnTRmmdxDbR58ykvqHUm38UU9S3oGRY7ZQLaNFUYsiRiammCpXsG4mGkvKywkQrHXYWWBwM3eqfzmcdeAE5xTWOJSLCSQkwmdvZQW3Tp3H4fICnI7wJkts+sL9LLnnBGHWxxk7He8xHfe56VplIzSwzjEeh8kFEMHEhgvaumR5kCFWKn08NJ9wzgVdu7rE/ZqzsZ9EL07c7p5N0n/LtqKf4ZWCNcZY98jJA26qWkKLIjIxE4USJ8cmmSiUieI4SUwUOGewzmKdxRhT/7IYa4ltcttZh7NS/9smIHUCThBnCVRI1QbcW1zPPYVNVMRDogrrBx9k8R3HCLMBGFu3eA2wz61VGmfBOcomrsdACWTFOa5s79ZRuWyibPqcmx955J3b+rfFosS6vl9fEJ6WL8zhZLZ8WuMMDvaanp4B/e7vP+vHNlt7V6DTOo6MeeTEQXeyOJowXHBUwiqjU1McH5ngxOgUE1NlqlGcAM1aZqLEhBfQaLHVS964Okimn491OAvGgDhDSsUcjzq5bepcRk0TeCEbvrGHhQ8OUcvoeluv0aVJLK7FTYPSAZExOGumC9nGWjqCNJvyrapQLtpSofpn5l3f/ID75583S7/YX1cdw9M6CXE9A5qNu5z0zyV4Xn11n3fLLf3xXzzzW++3hfRbSrWiMWKkq6lddefb8bWHtRZjHaYe+2klaE+hlEKrmV6uyKxORn1ISVTSXktabEJDq2O69SegcBg0zlrOye5mqR6ils1zx6u2UGxP40UGWy8FOefqXj75PbGDfKaFa/LNYGNc3Q5qEUaiGoPHDlDV4l713THJHxm/v7hpwQubXnjxrl/HWeXTBoCur09Jf7892fuhD+WC1MbYk3e2fvY1dzT+jZ0ouje57Rt3ue39291gz6C68aZes/36b/1lPO79aRjViKnh64COfDttmRY8UVg7EwM2EhNjDcbNxGmqDjRnBWsTVyxIAkRPCHyPlO+TSfkEWqNE6nGkIUawTjgvv5sV9jhDqxdzx8vPQUVmeuzEzsq6nSi0rXLm8dtZu+FZkGrG1ckVyYSA4qvHD7KPkCt/PhRfen/JMxk9YjtTzwtes+2nv24gPO0s4HDPh+7r7Og+e6o8FYnjC8ZEH2770hvuPfV+Az0DenzfuPr9e18T/dUN33hxcUTeV6yYbq0MWCee0jSlc+SDHBk/ha89nLPTFgwBYyxx1SbJhhJ0SuGlFUHWQykwsSOOLVHFUCsbnIFMxqelOUM+l0ac4Jwlckkv+ZLc/SysjXDf885l3xVLCUo1jFLTZRjBUPVybD7072wqHaWSWkTmwpeDiRLn70Brzc/HhvhJeZQNh8o88ztHjcpntXFu3K5pfUbwwktvd84p+TVhWp8+FrAuHHm854NfW9jS+uyiDcl7KT1RLVmEH2od/DCOaj8vT1X2LfnG246cOgm365Z9V937j3fvePChqhT9DLGJBAxpL00+SJMN0qSDDILChoa4aglyiq41eZae1cyCM3K0Lk2RafEJshqlktgvrFpqhZiJYzVOPlzm2O4pTj5cxJahtT1HUz6DiCO2ioyucVnmLqTZ46evvZgwqxFj60MqlkhnaB1/iKuP7SC49CVUdn6YYONLCZafjwtrWAStNI+VJvm38eN0jIfc8OV9ZPMZo5TWRtyR6LyFV2aecd6Bhsd4sgPwtGFh7KwrGNhKeHscRDcQEBdNzaTSKZ3RwbWgry1bcFlbHun98GOHw/edrJarR6NqvL9Ssw+ZP/2nF56PUyu0uGOqQ8bT7VT8dozOY9EYB3G1hhdF5BblWf/UJWzY1kn3mmxCTJ2p4tUrxg5EkWrSNHUHdK7JsfbKDnCW0QNVHtk5xgPfG2L8cJHuBa1k05qiTXF/fAaXnLyXxXcc4+FrVxKU4iQWBKyL2Xjkp6TPeAqSqpJfmKO497sES85OyAv1ulDO8/GdUPMUoTHkrdXGl1iTWsoDJz7nnHsKvYPTujf/I4PjHKdTm++0AWBjdsP48m+jlam/TKuM9lMB1jhXtjWLEyee6Fwqn/XRm11sN7vmhLlSDSMsjqlyhZy1sspVwTtJrMepOp/YT6NqFq89TcuzN9F6zZn4LRnA4GKHqUX1yyNzmC7Tfd063caRJCgdq9JcumoZZz+3m7u/epx7v3aCTCGgszvH8UoHh9UCVt17lH2XLiHSoIyh6udZc/RHLGpqQ5auY//dR2F4Ccvye6k+dhvp9VdiqxWQZCJPATUcxzZ00l4yyHjNs34t1ipzVfThH/5pMNj7525gQNPL/yQedKe8wPkyzPRHs7/fur4+tfxrf/RgrVa7hUIoURRZpUVERCslnoiINdZVTWxDz5o4o2KT07FqCozKBra5vYl8RzPprg4yHa20LWhh2cIsq7Mha5+xgrXvfRZdv30+XpOPqYXYMCm3KCUo3eD6Mc31a4wMiwLRyX1EwIYWUw3JtWmufNVKet6/ieY1AcMniygxPOStwh+q0fHIKDVfEaHJlo9y9vgu9PoLMeEon3r3Y3zxH0JUzqP66Hdx1Woyl2KpJ06gYkt4/nJ4wSW4jIeLY21daHXVvXPo87ecL7295r9TI2wwbD6w574zvnfs8PMBThe5kdOrDrh7U/LxjM17qmGN0mTBWWdRWk+3txARpUUJonF4IuJ5vqeDbKDS+TSZ5iz51hzZljyeE0j7yEuuRl71FGxXC6ZawxmXgEnNAM25U33Vf+zcRIHSgo0dphqycEOO3/67M1m5tYWJ4UmKZDlWbmPh/SexzhErj81HbiG/+ExUa5qvf/ARzr/0TBZ0X8ydP2+jKTtM+bHbEC8FOEJricWhLXTmstDdBC+5FGlKi6uGTolOtY7U/iqZDdz+X76tg/XrbIQrp6LaiwB2Dw7KPABPvbCDvWagp0ev+N67f1Aw1U9nrPaGjg7H5WIZ0YJoNTNInvSxEqiIJPU9rdGeBk+jrcPrzOO/aiv+tjNQ1iJRjNKKx3lZd6rL5fGIdKd81a2j8gQbGpRyXPtHqznreV1Mniixzy0kd7SCCgMWjd/LaqnCuo0ce/Aod91c5Wkv2MzSthX86NsduHSe+NituDgCC8U4wgBeCJ0dzRBHyIIW+K3zQIm2cdX6xrsuuumua6S/37r/ome8a2d9rAG3fiwO1znn1GBPj50H4BOcnsEB6+hT+a7sG8cqxfuCqvOGDh6PR4+NUKvWEmqVp9BeAjgv8NApr15jA5XyUcZBRx71mq2odQuQ0NDQA5xhbsls5kDyrdbg1788lQC8wSSYXTeQx1tEZx02Mlz26hWsvjrH0ZJPWM3SfPQoZw/dil55FqJqfPWDRZ71oqvJtXm0d/kU969gz8Mt5OQwlSP3QyrgeLVMpRqzJN9EtjWDcUAtRFZ0IteeiasahxORo5N/iBbYtes/Typ2JoqvnnB+7OwZQDP1dRTzAHxcmiaOPlj0hT8qVXLqtys2Ptjkpb3i+FR88sBxTuw/xtDhIUaPjTI+PMbw0WFOHDhOrRqhPA8ig3TkkN+7DLryiHOgZW7RySWAwVMQBBAECYt6qgoni3CygBuvQGTB95P7aDWb4PeEbhkHNjZse9NKOjfl2HeimfN2fYOOBatQS5fzky8dRZlFXHTtciJnSeWFNUvXcc/PVgA1oke/h7OOY1EVG8ZsWtpdv0KJiitRiFy0ElnbqSmWnNTsU2s/fvQs6e+3/xFpwTkn/f399u/23tvtLFtsOqW/dWz/RdQH5uez4P8kIZH+dz/26Fs+eU18YPxf26bUlrFKyVXC2JQLFe2sE2sN6WyG7nVLaepsTXh91kLPBbCwKcGblieUY5PAg4ky7DqO2z8C4yUo1JA48UziKcimoD0Ha7tg40JozUEcg01EVt0p8yGiEsaNl1Jc/LLV3PeBO1i8LMJbdQ6FYyP8+Cua33vzFgojMToj6JRH94IM9z7Uzr7jnaxuP8rex+7niOezua2NJS1N2NjM9KltXbFh63rsoV8YpVKeemy4B3iwLqz+OLf6ibvu8pxz8Xv23HVRNpdrdQjDteqrEbl5/M47G/IQ7ldncE7jM9DTo3sHB83w8HBT+e2D74sOj70qXXVSsiFWQeuiTjqXLUR7OqGsWot91tlwwQrEWCQdJBy8OQTRepp7637cnfuQiQqUY8SY5HekPEj5yX1igzMJWYF8Gs5fBletg4wHYTxX4HI2yBFMYZTyrR8mc94leAuyfOodB1jWfhXXvXAd4+Mx6RbNvlsmOPCDKY6MTNG87mZe+Px9/LC6iVvXXcsbFi2mLUhjrEXNfv7OQeDDTfca9fCoNu2pe/VrrrwAEdvg4vY5pzaB7Nq5U/rrAkrvfejeb6fzuevDcsV4nmebQ3P5yzdsvmPADehdO7ukrmMzJyL+jbWAjdM7OGhcX5+Srq4Cmtec+Oedny19594XpIrhS9o721tyna0OZ8XhoBRiL1wBF66ESojk04niwSngECGxkhsXIOcuBk9DKcSNleD4JG7/MBwcg2INSflINkjiw9ggP9mL2zuM/NZ5sKgZwuhxI3LOWVSQIpw8ycSRQ2SWdnNy9yT37lzAhhvyPLhjlGxLCi+lGL4zwjjHujWLuefRlZw48hBnND9KPv9c2lIZrImTeeNptvYseJy7RLldx5HQO5vHRs4VuKvRopstiPQXD/xiWZBK/4UfBNdXiyWnBLE4f1S7r7z34Xve3CvnfW2+FfffqGNtF5H+uospvvmfb8oFzc8zLopFiyfW4jI+7lVXQj6FBB7i6zlJbQN80994aibTbRT7EBwWhgrwwFHkvsMwXATPw3kq+Z3Gge/BCy6Ale0JCJXMVVrFofyAvZ/5I/zSQyw5exUf/NBiJh65mCUL8vgqINeUIbaGA6PHaWtOs//4OM/r/TGbu+/Hv/RdZDdcjg2riPJmvwKm6a4O+PTPY1UWz5zb9QbvKRv+we3Y4W0Hyh3ZcwPlbW7y9Tm+Ur/j53Ldlckpp5SSZEw0dn4qLUoJ1Vq4oxCH31BaPdCZ0ne/ZdV5E7/RScgTfkpE3Pa+PtzAgB5/7gdW6pq9EjEOcRoRXGxg6xnQlgPjEF/PyRdkrndMTmwTMBmX3A5jqIUQxkhXHp66EV67Fff0TbhAoFxN4j8luEqIG7wLxsuJBXWnfJTrwO685PmMHB5G8Hj6syYZN0dRnuC0IQxDjo4NEUYVHtl/gtaFj7F6wQmODQfQtjSJM0XNGb5v3BabfAjc6g6hEuEq4cUAbNtqnn/22Yu2di78m9XZ7Ec6urreFDQ3ddcKhTjp2SUeVitP4lotNsDC7q5ta3PN77movftPtrUvO6P+gVfzAHwiIPb2GtWZ/+t0c1unMZEVpURiA4tacecsg2qIpP1pnCmR6dmMuabw8eUUJ+BUfc43tkgY4gKFXL0BXrcNNi/Blaq4agi+IJNl+Ob9dcs5N3ISpbBRSOuGi8mvvpijew6z8YyQ7pWPcnK0gGiITYxxMZ4LkPQEz33aLkqHHqJz6++TXbACG4czM8d1AaXpeYLGjN2KtqQeWaguS+64XTZ3dBx+3pKV17x81YZFV9vUda3V8KtekPJQCudcvbJkbUtrq3dmKn/bU3XTDS9fccai53Yvv/bcls7b6x94Ow/A2QalzvyYfNH/OyPIpJ+Pi60opURJIix04SoI6rVYX00nGrGxqCCY1UVpxGl1Y+Jm5jamvxpwFUk0zWsh0p5FXnwp7llngzFIFEPKg4eOw8PHk1KNc4+3ggKLr3kZY4dPEhfLPP26ImO1cZxzlMMqNVPm2ORJrrnuYdrjXahVz6Droqdjwxqi9Ez9MaiXglJBcluS3y+dTcnrHirXH7vfAYTOISKF9Z2dN//uijOe7xvzMqW10UpZY6xNZzNqs5/5+DMXLtu2orn5GyIyiXPyq1BmeHJYwEaLLuO/Md3U4oO1opQQG+jK4TYuhFqM+F4ih2Ed4nnsuu9RPvxX/4QOggSQUUJeSKbkLHFscNahtEYHAToIUL6XTK7VJTrQApGBMEKu3AAvuRSnBGoRaMH94iDT9Rg3k4yIJFawac255FZs4djDxzjvHEf7kr0cH55CacvYRMSZ5x/nolV7mKgtZPkNb8aZetHcuqQgrjUcHMX9+GHczbtwu49P1yRd1hdSCnyWO+vyAtPFZeecDDin+3bs8N6w9qzPhrXaR71sRknKV92ouy7vWPg6EantcC5R/09mE37p5Zgni0a0mfqdj3dqrV/gbIwFLUogNHDmYsinoFQDz58V5jk6u1v50PZPUi3WeOtfvBo/k37CxyhOFShMFDFRTDqXpqO7Dc9P7mvDGs6StPBqNThjMe6ll+O+cCtSM3BoPKkntqaTWHJ2rFm3YAu3/R77PvtmFq4psO3qkG8OnEE27MLLH+U5V97L8L6TLP29j+I3tWLDGqBwgYeMlODfH8A9NoREDozB+Qq3YRFyw7mQC4SMhwttRxmageL27duFZOOEA0yfc6rPOaX23fX+aqn88rbW1qYVkvqYiNgdznnbROL5QvR/drZu10DsfHt9NtfSbsUZJaJBcEpwq7sSCyUqsQx19+mimIVLuzl3y9l85G8+w523PEDPK57F5ovX09SU4+TxIe657WFu33EPDz+0l3AqxsaGIBOwYGkXmy9Zx/W/9RQuvPI8AEythtIaqjVkRSfudy/Fffo2pFSF0SK0ZcEZpot2DSsYhjStPY/sqgs5/vAetpy9hB99/1Hu2T/M6199D25oNy1XvI7WMy9Msl7RSYJxeAz3xV8g5RDRAqqegCiB2w/gKhG88sokKZrmeCfUhP5Zb1+/iO3r61Pv6O8/1P/gHfe4WnjVpctW7Khbyl95P/hJAMCEJyhaPx/fc7goebujGNrzsKA5AaCnkotTD8Xi2OBn0jz9edt48PZH2HXHw/zitnvJ5tLkc02Mjo8RRTFZshgV17sMMRExh48c4xc/v5uBj36Hq66/iDf0v5RN555BXK2hlCC1EJZ3wW+fh/vC7TBRnpbeSOLKhsr0TPV74dYXs/eTb6BreTNXXbGXsy/uYk3rUcbtlax+xsuxUZhERFrBaAm+dDtSCpMs3QJru2F9N645k7zAo+NQDaEpjYS1ShZqSR6y3dHff8p7uFXR3++cyJ054zYBRyTpBTMPwP/a/dqpng91ichVuDjJVT0NkcEubcNlfKQSJq216SqcoLXCWcNvvezpfObDX2ZsdJzWXAtxGFOZqpBPZVFpRblYxkvDsoXLyDWlUVoTlg2jI6NUqlVu/uYt3PLDn/Ou97+JF776hgSEWiWWcPMy3MVDMFZOKjENlkxDTTphsGKjWhILrr2E4UO72HJ2luLQvYxMNLHute+aJkY0Vsi6b92HDBcgl4KNS+CyNbC8DSdquhIom5ZQFygWEX0CmPqP3sdNW7c6wAXau7fJ8zeLSNgzMKDlNJD+OL0tYO+gAoxJ+Zub0pkWi7UiiTMS52BB00xxWcmsjliSFJgopqO7jXd+4HX8wY19KDTaE5RoojDC8xQvelEPl196KRs3radaCfnJT2/ngd27uPfeeymUi+Rb8pjQ8s7X/C1TE1O89o9/j7haQ3sqoU9dtxFqMZj4lCx4LnMMYMGVN3LwC28j320ZOjLJqpd+kKC1G1urJWRU38fdeQB+cQA2LIDrNsMZC5LfEkYzAG/o2qQ8BwqagnERCR19TzistGv7dgeQ9binK5NvP50u8WkNwOk5ESXn61QaCwnro85wka4mrLEJCOsATC5SclsrRVyp8qzepzE2PMV73v5RPJehFtXI5NP0v/tPuPSii9FWccd9d/P+j/wjjzy8F195+GmFMQ5nFH7Kp0nn+cu3f5glKxbx7BuvJa4l7piUh2T8xFWKzAFcIzBz9Viwed0WvEVncfCun7LyRe+lZd352Fo1KbnU41Z++BCyZQXuBRcguRSuWquXhUAp1Qguk2w/NBBaXGvuKAA9m4TBx7+P/fXhpTetOWc3sBtg8DQZ7TytyzBbuzcl771xFyRGxdYtQEKlsmkvkdXlFLLBrFkO7SmicoXfe/3zecu7X8VEuUBExDv/9K1cdsklVEoVfnbv7fzB2/+EfXsP0trcTCaXolYOaW1poaWlmYmpScCRDbL89Zv/gaEjw2itcXVB6MZzOBV8bk7zJXlyK5/7Fla88L10bnk6Lgxn6n2ehj0ncGcugldcgfUEWw1R6QCdTqFTqWldmen2YTV2WEGaU3cC8Lou+S86SvZ0G+c8veuAAz3WgRgTL8KZugplIiDkPA1pPxEUcqdIQ54qPiTJwHmhUKBIiadcdTVXXHA5k6NTjE9M8Ffv+RCEkM9nsc5SKJa44aVP5+v3fpKb7vk4z3vZ05koTtKUzXHyxBD/728+h3jerMedWWxTX8P+uLq0iMKZmOyidXRdkBSbp4kMSnBxjKxsh+s3YqpVvFQKnU5x7NAJ7vr5vex7+CAqCNBBChPFSQVgvIIB9OZFcSNje7Kd0xaACeVX3OG3/H3a4dYYE+OcVY2eqPgatJoWJ5/j8hq3ZdbGI6WojDuyNLP1sqsRBYvPb+OmH36L48eGaco1YYyhVquxYGk7fR99M92LOliwuJP3fepdnH3OWZQLNTKZNF//0vc4dugEXirAWje3q+dkVjI09xWBYKNa4nZP4YGIdbisD8bipdPc+bP7eMUNb+V5F72WFz31zfRe/Dpe+Yw/4tFde/GyGZRovNEKenUHI1lJPUnxd/oCcHvfdgHIjac7ldDSUJWaLm6YWWyDWWOTzs11xbM1nJvSzXSphWy+fB1dl2UopCb5wbdvpTndhDWCE0c5LLN63QpyuSzWGMJahCBcue0iKqaGl/IZHh/lJ9+/vW5ZzVyMMQuQjZ5fPYiTeh1PlJ6xzrP/Vws68Hnvuz/Ki7e+mW9843scOXkIWzbEUcgPvruT37vuTfz0+79geHiUvXc/Kh/5xL+4j//lp89VWujt7Z2lqORkYGBAN/YcS9IXn+6O9D2B+NN8EjIbgPWCqjV2gbKSj60hJcF0L1eMSeSqSLofLnYov16iEJmZHZpV62rvbGFp53JWXNiNKLhrx24mjlZpbmsmjCoYGxN4PgcPHKJaqZHOpBJiqxJOHh9G46G0kJUm7vvJQ9z4iufWFx46Hp/zzgIWieagzALd7LgwCRcEfOGPX/3XfO5TX6GzqZXXPuvlrFm9kt0PPsI3vvtvNDc1MzlU5jXXv4P2ha0cOXLUnXnmRvnHd/7lD9/152+gp6eHwYEBGQDVK2J66yvC+mdiQAczc8Q9AwN64Fe8ava0L0T7EozHrloVS9rVe6Qigo1iqBmkRdHQTnP1lzPNjpotEg2s37SGhZ370PWOyd7dhxCnyfrNRHGIMTGpdMC+fYd435//I+96zxvxA58ff/92fvCdn5EJ0rQ2d7C0I8uu+x4GZ5N6IzOWb87jz3n02XB0c/7dOvDSAX/9Rx/hE5/6IgtTC8AoDu0/zmtf8XJ6n/PbNDU38enPf56O5naUCEeOHDOLFy32Xrf9Bd/acP66z/b19Sl6ekDE9YJZ8ZnPpF96wZlXBaKvNdZdJNZmY2NqNWP2jJVqd0dx7XufufZZ+4SEQf2r2up5+gKwf7uDfiJvYgidnlKOtLV2psxSM1CowsLm5P6xnXZ1De83zYJWgDOs27KYlpZWSpM1ss1pJk5W6M4vZUXbKvaEv8DYGLGOpkwTn/ybL3Lvz3bT3tnOL75/HzZK6PfNQSvnXnIG3/r+v1GrhKSCZLfIbFf/eFs4QySVObcTgSQvk+bbAz/kY+/7AlefeylWLAd3neRHP/8Jn/r0F3jj7/8+Nzz72XzvuzsYnxilFFXsGatW6Df82Ut++qze636vcmNFtm7frraJxNcMfLzl2s0X/EFTOvu7ytPrM+k0URRirSN2jqo1lzdFEeNjE8U33vrDzx0+fvTP+0WGegYG9K+iNHPaxoCCONfXpzo//cdFEdntxS7Z+NKgTBmDGynUt5+7+r43N4f1LNMVC8HUYtqXtNC9KseB+4fAQVdmCas6NrGwaSmBDrDUN3GKojnXwt0/eYBvf+37xCZmaesGtMuiAsumjRvQSmMazJXHgU0S0qidKQc5m6igTo8JkAwwad9ndGSUt71uO9c++woGbvtHBn/2CdafuxIlsOfhhyiXKnQsaqGjsx0b4P74bS+Rr/zV28ee89Jn/o6ITDz44IP+NpH43Xf//Lkvvuypd56zfMVfLM7n1wdxbClX4k5RJh8bawpFUx2biGWyGLdone9ua3v9GctW3v6HO//90sHeXtPjfvkimKd3GWb3pqTuovUJSeZu3Zz90ofHpgvAOAeRqQf3bqYXO3uYHMdTXnQWB+8bAYHOhckkndbQ0dQJTlD1P9ZZsvkMTdks6VSGFW0bWZRfy8JFi1jU2c2C9m7SmVRCn5qJ6JgOUtMpVDqFeDopVqdTOF9Pl4ekPhoqnuYTf/svFMZLbP/wW0mlA9KZgLO3bMI5hfMszWf62JqjMFVgzabV7vWvf6k059OjW+HEwMCAPuuss8L37rr79y9fueLra1pa10ZTxTiD2I2tHcqPrHfrw3v1TXfdo752x536+7t2eTc/+KB36yOPuvv2PByNFYorCdLffffPd145KL2m55csjP6k6IQ4Z+811rwgjiCd8qcvnDs6iSvWIJ3MathahAo8ZvECpmMvUWBrIec+fR1HH7uLciFk+TkdWOe4+OzzWV9ZxD1f+Dk65RG7eDqLjWPDJWuvJ5dpYWS8mRt6noGfFhYtXYDyPEylVrfCdewpQQIfs+sw8a2PYk9MgXV4qzrxrj0LWdSKqyaECi8dcPzICb788X/jnHVnsXTFIgCqUY2f//ROcjSRTeVoXp6mWChx6PghfvcFNzpTDAnz3sM7wUlvr/ng7nvesGXlyo/kYmuL1SqLcnmvVCzz73t28bPDBylXq6xob+Oy5avIBxlSvubg6Ijcf/yob3FmqlRpbsllvvnJh+66+lUbttz/y4wJT2sANjohUc3eV/NjQmKVymaTUVatcONF3MERZNNiiCNcLYaMqc+EzKrHyEy1RjnLpTes48CuETZetpRV65cxNRKR8Rdw5ZlP4we7v07KC3Ak1vTyldezaeEFTFTGWLS0k60vOocff/U21p+1PHGjOPQpZILKJ3+E2fkQfmczfnsLaI29+zC1nz2G/+qr0VtWEZcqqFTAv3z265wsnMQet/zke7/gvEs38d53fpy9uw+jxKNtQTPOwVhlFJzmOddeiq5aaitad2RFzN/df2fv2sVLPuLVIjMZh2ppvll2HT7Kp+66g/FqmctXrmbb8nWc0bGQjkyaxjx+FMd86oc/5GuPPqCXr1oeT4Rh690Hj3zGOXfZ9u3bIxok1d/oLHgw0S9xlejOkrjRwHkdYaXq/HQgztTrgvcfQc5cXN8R53CVEPEzc8sdbrohgg1jOhblCFIe2WyaC3qW8shnRzhj0zJeeMkrWNq5hIeOPoAoWN91Lmd2X0joqtSGDc9946WkMh6FsMRTnnl5vYkhiTK+FlQQUPjgdzA/3E3TuavRrU0JfaolByu7sY8eJfr0j5GWLN7KDqJqlVu+fhdNqpW4Znjz7/QTNHuMHyqxbskWDh/bz/pz1yICP/v2HVxx1WWcv/lMMfefoPXCdT95wQ9+sKCjpflDtVrVHQlD2dzRKT/cs4cvPXgfi5qbecV5l3LF8jVkfSE0lkoUTa+oQIS3Pes6Dn96mB/eu8s7/4Kz42I6fX7/T3e8tr+//0M9mzbpQfg/T0pO6xhQEOd6BvSSf/vDERuZHwRWXK1YNg0dFudrzMMnkliwPhNiqxG2Fk/Hhe7URrEIJjI0tfrYasi2l5xJ+4UelbEa2VSK5235Hf7wWX/Om6/r4ykbrycVeIyeKLH2aW1c85KziSPDsvWLOPfSzbgwTITMs2kkFTD1r7cS/vghcuuX4Eo1bC3ChRbnCW7TAtTqBXh+QPTd+xDPY9+jRxjZWyVIBVgVU6lWOHlkiNb2FjoyC1m7eDPXPvdKAP796z/g1X03OkKjdFeq+u2xY88+p7vltmwqWDhRKtCSyagdDz3Klx64jzM7uvizK57OtavXkvYcgbK0phStKQ0IWgkKx2jF8JYbbiBjhKOHj6k4jt2RwtQbnXOZwd5e+8uYETntZ0KmGTGarzqQaqkiYalap7wDYUz844cSiNWnx1yxOmtOw80UPRpjjSJYk+wCSWt47vaN2DVlhk5OMDY8QaVQoTxVoTBRYHRyktXPyXLjX16Q6Mc4y5YLN9Co/tXCiKEv/JjRN3+eymd+RqYt2S9XmZqi8MhhJDLQnEbacrizlyALmgnvOwgjU+zZdRip5VBa4eET6ADtKTYtuJQsLWy6eAVrNy3j+zf9hA3nrOXybeeL2z/MUF6ndk2Ov7uruXnV8MSEy6bSsv/4Sb50312cvWAB77jiOlY0t+ArQ95PBC8bXSGRmd50GBsWtuXZumkT+/YeUGGpRKxl9Vd2338Z4AYGB9VvPAC33tKfSEFtWvftibi6J608VSmWrHMkpZeUh3nwKOaug4mKgXW4yGCnKo8fBp4j5JKo4NvY0twccMNfn8GG16bxz65QaZ8kXFig6UrD09+7it9+5/l4gIsilEv4zjYyiO9Rnqrwk7/9Cqn946Q78+CSZChIZ0h3tCVMmalKorwggvJTuPEq7D1GNJHlnO6L8cSnFlWZqoxzycqnsWX5VRhj+a03XkmpWOGunzzIO973BmylhlQc3x07LpVKxdbCmg1SgdQqNW669x4WNzfzBxdupTubIa0NgVKzVOaEamzr38t0MTwyjs0rVxNZS1wNjZfJuMemJi8B2NXV9X9uAU/7ToiAcz2Dekl/b/lg79+9XaG+aaPIVAtFlWnOY4wFTxN+9wHSyzuQjhy2GkE5xCmFNKWTepzwuEJxQ6XNRkkheeO1C9h4rcOECblEBz4gmGo4TXKd7mSopBvT1tHCcMrw0PAJtnSvoxDWcBWLF/h4GYcTB3Xw0ZaHlI/KpXHFEinVxJqODUjXNu49+HMuWHE5V667noMHh9j24s2cd/UafvC1W3nBq6+ntbMFN1LiYGWKe1oLLJMWVTWGBek0O3ftompiXnX+FSxrbsZXFi1qFh3MERtHObIzBXMnaJVseV/U1ka+uZlaGEktDMV66QsF6K/Luv1GW0BoCFcO6BUDf/Styagy0OKnvXKhHFcKpaSupsCVa4SDv4BKnAhZOoctVXGlWjLU80RdCmGOZTTlCFM2KKsQK8n3lWiaYv+47p4DJ47zly/ljr37OTo+QZP2sbEhjmJMsYQbGk90ZoYKMFpAPLC1iPDEBN2rmmhqSfGiS17BX/z2R3j+lpcweaxM+zma3ndfzNR4kbPOW8PKM5YS2RiZqHFbqkTkK6q1EC3CoaERdp04xjPWbeTipcsQDJ5Sp2xvh8nQzrDF668jpQUFBL5PNp/FOEtkYoq1Wv6XBYwnjTLCrsFdro8+5Xep10+GlccyTnuFsUlTK5WTDNjXxAdHKH/uJ8mQUtpP9PqmKpjJcl33WaZ5esLj5f5EJZUHV7d2Sqtp4YM5eG38BmtxvmbJGSvYtvFMvnXn/Xzz3vuITUygFbGx2KkSjBaSKbaJElRrRKUKpULMuVctouM8n2NHh6kWauw7epD2pyhufN+5aLE05VIsXNmFiWK8SkRt9zF2BSE5oBLHWGu579AhupuaeO6Z54BzpBsUtVmfrcmqpWYao1IzVjzQghaISSx2wzp6ao4k5zwAE0ZHv93eB0s+8YcjYdq7MSSe9FF6amTSVCaL9azYI37sJJV/+jFusoLkUzgcdrJCfLKQDK83ZkfsLKmL2forp7TWZBbyZu0+ny5UK1GkL11LPvB5zjmbGZuc4rM/vpWHjp0gpTQmMtjJIhQrMFHCTVaolCuold2kUx7X/elKlr8IOp/juPo9i7mhbwOZQOFikzCgKxGkUsiRIo8eH+IgFVycbH8anZziyNgoVy9fy/LmJvSsKcvGCrLJmqMUu+k1ZI3XoZUQ1FXZh0ollK/JZTM4hHyQqs4D8IlccX+/dT0DesWX3nTXhG+eZ7GltHi6MDZlCiMTmGoNnQ2wx8cpfuRmqjsfAguSDXBY4nKVuBpiPQVZf+Yr5c2oqDa2Cc5ezXCK/52mE4jgooiWbWcxrmMolum94CKu27SJn977EHc89Bg+iqhawxUrMFWldnKS0IPsOctxxpLLB1z4/FVceOMyVmxuw1YM1iQCmOIcBBo7MoXdfcLuX+ZTMCGlSgVrLEeGhklrj22r1lGL69zHOs4iA6PVmHJk0aekEtYJWU+h6qIPx8pTNDfnyWUyztcaT+kHHXD11v97fHg8yY4M9podV/d5Zw68fcfht3zq2RwpfD1Xcs2lcmhr5apKN2UI8hnMWJXwq7fj33mA3NVn4jeloRhCJUq2BeZSkPVx+RTSkobWDLRkknpibCGK6+Sax4sPuVku28YGrylL9yufyoE//RIuE7C4o42nbjyDr9x9Ny25DGuWLMRUa/giTB06ibdpGcHiDmylmlDrK9GM8Lmq82WMw3kqQch3H7Gqs0Md6SpjD0YUXY2MHzBWrbC2ayFLm9upxQZjILKKyDjCuhNVswRiG89bK8j6yb67QhhztDTJgrZWxImIc6xubXsIYCtbuYX+eQCeerbd0h/vuLrPW/aBV+44/PHvPU1uffST+vD45qqLnasoIZumtaOdTD6LUhp+fACX9xOPqxKmioQG5Vwi76EVtGawnXlY2Y6s78Itbk6uWBjjRJ4gg0n8nFKCrdZYeMOlVI+OcfgT36Ml30QQpLhw8VIe3H+ElYsWQKVKXK1ybGiINX/1/Fkq/DInzpwOD9IerlSzfGsPflub4vJlH7jl5ttbfN9/eRzHxhmji9UKqxavJNCKMI4xSlEKbV0VdvbSHVcflk+4Gy2BSmI/J+ybHGPCRHTmm9zJySmdD+Pqc9ef+VOA7Vu32v55C/gfg9D1DATymutuJ5c6++SbPntfe8WenW3JWs96yjalmOzOUVzZSqUjTSXnE6fqUr6ACg3pckxmpEzuSIGW40WCx4bgsWHsz/chqzrhijW4ZW2JAoGbk4VMu+UGBdHGEctf8lRyaxay/zM/5MieQzShmBgvc2x4lFVLF/LgT+8n/6LLaTp3FbZSBVUfNJ9W6pekUZvynDs4ZvSPD3i0NlG9oOtvM83+Oy76u795ReeSxS93WlzJrxHVIpa3ts7Rx2wsA3A87iljHWQ8IecrjHWUI8f9EydpzWcJHLaCUxtbWu8C9if1+v97QsKTEoCur0+xfbsTkfDBnr5g9ZL1PZlUbhkdGVdpycihtS2MrWmh1pZJaoHOJVavMcXmQPIB5Q7BrWjGnr+AYKpG175JFt5zktxwEbfnBDw6BJeugq3rkgc2tk73nz2FN6vZ5wntF62neeMKioeGMJNl9M9388jgz7DHJvEuP4M1b30uthYm4GsAR9dXQojgxkpG33tCcyL0TGf+qLt65RszufRNfX196tvG2mKxhPG0tGYy+JkM2VQGY0+pbU7TXpmOYROxLaE5UPWVtcKjhXFOhCUWNbfw6OGjpFOBXLh4yaCIuL4dO7yGvvQ8AGeDr7Evt7+f8tu+/JIgF7xV459tF7Sx//xOjq9uIc54+LHBCy2OU/l6jbVBLnHBJMuno7TH4XO7ObahnVW3HWXp3cexAvzgITgyDjdugUDjIssc1fBZgaH4GpfycIUqTasW4KUCms5axj2HR5AzV7HhD5+TjA/A3O1MQ0VcoYp+ZBRqoi2mpDZ3fz48e+FfZ0UO9/UNBP39veFZf/Xn47paw1or1aY8OEsYRaiGCz9Ftr9xy7ik5teaVmiSEHe4GnHn2DGa0ikIjTtcmFLndXaPPH3Vun+pu1/T/0u4nk8aADrnhO2I9Iopvvnz56fTmb/U2dwzEMX+5Wl7YNtSkfaM6NCQqibi4Wb6ItfLJnWT404pQDeGl/xKhFXCo09dSbklxbrvPobLpeDhk/DFXyC/ewlOJ3Mp03EhMsfHSdonWNRCPF4mKlcJmrJc9vm3JSXgKMLVh5wa4pgohX10xMme45i13QVZmv+cOm/px0RkT/KBc1p2bY8B0lbuqhWK1Zox6bCzzSmtZTKsoqi/pvpzavBzbf3F5XxFc5CoKRjrmAodd4wfo2RCujJZfrL/IdPe2uJds2r1B0RkaOCXqBvz5FBI7RnQIuKkX2z1bV96S6qp6We6rfUZ4MzPzmu233vKAnVEhTI2UaAcx8RSn2FHZowVM8SEmbJfQxm13rBSChz4xZCDFyzi4CVLUNUatNRB+K37E4XSWQXpOTBsXHmt8Dub8Be0IE1pbC3ElKsJkXZWWpqwLCze1eusbslJdd/Qffr8ZW8UkT1uwGnnnEivGPr7LX196s53v/uws+57xkG5VDaeCA8PnyROJIqmy0O2bggzntCeUbSkVH3rhGMqhPsKQxyuTNKdb+KxYyfM4XLRO7+57f6nrlz7ob6+PtXzS1zjpZ4U4BvsNcMv/9um8I8HPp/qXPB+nU+nbVg1O67s0vdsaVep2GFjw4SJOFoucqhY4HC5yIlqmeFqlZoxyYWZ5S+tc3M6BtMDxXWt6Ew5ZM+lizixIIsqRIkI5p2HkAePQjpI4kl5okFMmR61FF/XC9/JnrtZbdg597VxrM3T1tvg4Phlxfd/5x0JMgeZPS7ZsylRifXgfel0mkKpSsbzeXhihEOTY6Q9D+ssOV/RnlJ0ZTStKUVKC8Y5qpFwshKxpzTCybDIurYOJscn7c8OHpDzuhZU3nTxFa8UkdL27dv5ZY5pqicD+Iqv+8y5rQvW3uJ3db3Y6iiWyZr7+TnteteZreTLJqnH1VWjFELNGApRxFitlqw9VYJ1dq4G9HQ7rm4FT1lmo5ww6mLuXtNcX0qTvFvu5j1ILZ7ZIzc7FZG5lUJn57bE5ry2xv1FIIqRjiaR55ylMiPhe6Jv33+99Paa2UsIB3t7DX196q53v/unHe0t/0w67UXlSlSu1fjifb/AU0KgfUIjlGIox45yBKVQGKlYHpya4K6p4xRtjZXNrRw4dtze9MD97qwlS9RLzzzrDYHIHQPO6V+2dox32oPvtf/0jFRLy796rS3NJq7EOjTe8UVp7jmvnXwpySYbnUurkrqcKHARLMxkafb9xNrN6v82xuXmlCrcXLnQqrPUylWOr2mieJdHPrbYQMOxcdzDJ5Czl+Iq4UxCMisNlfpi8nrsOmdk83GkCCEhT4ShyLnLrP3Bw4Q7H/qIc+5nyPZCXdUgiWS3b3cC6vlnnvWGL95+++oC7oq2zhZ7z/BJ9cE7fswz1m+iJUjY4NY5pqKQQlzleK1IKJb2dBYxju/ce7+55fABfc7iJbx87YZ3bupe9OkB53Tvr0Av8LQE4EAdfIXXfPLaoLXt615TNrBh1YhSnsMRiiUVQSXt13ueCqwlVQuRCjCpaFuSIed7xNYmkVojQOeJN7HOaLkkBdwT1QouNkTNKYbbM+SPlCClEyGh+w4jm5fO0SWfXaOeFrBiJlmZ/ZhPaA2NRWfSqnL+kjj7jQdXl//f9/8wR/+7Xe8mTZ0aLyIO53ilSOFD3/nOM/9t76NfCSNzbS7w7c5HH1aPTY5x5pIlZDNplCgsDk8JvlKkDG7v0WP2tgP7ZTyO9GXLlk++avO5r1/T3vXFnoGBXwn4TksAJjW+Hjv2ex9fnmpp+Re/ORdYE5lkQbUFz2PhiQrXf/lhTi7IU0tpNDFezVGImxgq5PEvTNPSliYOGwPjrr4jQ6YH1oUnFhFSAicrFQpRSIAQamEinyiyurRCBR5u/wiuUEn6yLGdYdk8bhpvRo7jVG7sqUFWsnIiRp25UBe+ebfzjk+9oXRw+GOyouuY63NK+uuuUcSt/YMPpd50/fVTZ7zxLR93R9PXLlm5xLYv6FSjk1P8ZGzCdLQ0uY6mZkn52lWjmOHxSTVUKKjQ13p5UwtPW732u68+94K3isieX9VA+ulrAXdvEhGx1bd88ZN+W3uHjSuxIN5s7pSXTtEdGhbvn4QoYty0cFCtIArytGx0uLM1Yc2g1GzAMa2tJ07muOGZBdTCiXKZ8bCGV89orYOKB2AT7CjBjJfQIwXU6q5kS9O0vTtl95kwSyhpVuY7t77UeHBcbNDtTVJrSZmmWLeWfrDnZcBf7WT77E2Ysvcjb6rR8+K1LUsWvXH9qpX8/Me3qaG9B1hy5lrSbS16LI4ZmhhPaFxK4TvH6s5Os6at7QdPW7H2g5ctW/7d15iYgYEB3fsrFqo8rQDYKDIXXv+ZP0h1LXiajSqxOOc1OFG27km1SmYLDxQ1J2pLCNMrMAguqsL5XrLxrQ7YhsttyLXJdPllJmjTIsTOcqxUYioK8erui7rvEzMLWc7hahF2uIBavWCawnUK23/2Huy6SurcCb05ZNhZ5lAFHrTlJTow6dRoume/c39/YOv22PXt8D48dpN+04kT8XOefu3zVi5Z+pmHH3ksHzjjVq1ZqR595DG37+498uobnvGVwzZ8QAf+ShfbSmuQGj1r8aJHnr9u471ZrR/8Y2uTz2B9/cWv+pp7p5Xr7e21k7/7ifVBc/PfQGydc7pxcZSv0J6DMGbfsGPnPotKr2bFwiV4NkbXDLXNYBc4vFpy5a1zszQDZXqQqGF0tJf861Qt4kSlTM0YPCV18M003JoqcQISU3e3cYydKM3kHadoQ7snUCaSUxOSRnPW1d1v/YmJp1EdWZm6+5DkFjZtWAltq27pP84t/QAxwP7la97wkuuuy//+FVdEf/alf/WL1bK1ga+uXb/u2B9de90LRSR6wuXBIAMDA6q3t9f8KhWxTk8LuHu3CNhSR64vyLdmsdVIB76PtRBWqYyFPDbquHs4xe6xgLVL17JxyQJCE+JiRRQbZHViZmLrUJpZc+kJF7hRsFV+8ne1EDM0VaWQjsC5OpW9nlHbBCSp0NE2mgw4OWNRgY+NLVKJHudJ5VTAza2Bz3RqZw3K23KIyqfmuHG0FhMb6xWj1Il3/uu79r7ogzepmKcGo6XDV51XcKnutotv+t53rLv8Cv+c88/Ge3gvzgljcRQDwdU7+hw74ZZNu93VXa+T12/d6nqS5TW29zTRhj6tAFjfBWeGbnzfejtVfmEoI8RR5JuoQhhFPDaa4u6pHPtrKWICzlqylI3LFlGLk90aCc3IYIJES8XVJdwarg9d/xKIQ4cZdpRGqoyNV4mWOnyVzIDYaf/oUA4iX9NxskzbUBmbTU2zoE0co5ydC74n0CiaBqFJOiBzao0NEMYGFxokpacJDy62WO3UyPAIqaq8rnv9ytcpz+erd93FguOWi4M29p8Y4R07/4El61cgGR/xPMrG1YD4lm39caN8cwuD3HIa13pPqxhQFrZKTfTDU6Oji6NaGJ0sudZ7SovVoaiZmo3wFaxq62DdwiXUoihZbVDPcEVr7M8NbrHGa1XTs8DKgClY7LjDDlvCIUelElHLO9QKhddicfEpu94QcJbIg2V7hsmEFteiEeOwJhk4SudT0zbuifSxZmtWunIIuQBRam49pj6tZ8s1tJdJ7hwnpfKpkxO0rVtKy9pOO1UssfP+fXbYOHlXehlt41ldSC3lkY5Wfnr/Y9yqJ1zLonbe2vtbf6dEagOnyQ6QJw0Apb5GoOtDr3zYObdl4uBEd22oJje9887bimXTnVJl15ZukWw6y8Zlq5Kmmpupb4gIqSDA7KsSf9gQdzlcqj5YFNe/aiCekMpbbJuHX6tQylgi56HqnZDZQpKRVmQnQjY+MJq04erlFmssphahmrNJB8XY6RVhc0XJZ/WbI5OIaWb1DM2//rsw9XizFoEoxFqi0SLihNbmJmomVl/70X0sXbdcvXLbeXiBTvpXxvG0yNK76gw+fvh+WaEzPN+sPuiAHnp4spzTKwtOSJBlYP8rN/zrJe2t2fbWQNvWTIcqhzWWdXaS0prYJavs51ge68jnMskWzOMRIoLyBDwBDyQlhBIRG4GpGovMUW7PLwYzA75ppVPjqOU8LvzRQTqmIky7n0j1+h5hsYoRh+rIJxLBoUk2qMvcwvI0OSE00wBzaW+WfjS4ME6iPqWw5RCsQ2UCKodHyHQ14/uaHbfvYeGaJVz7nEthqoxp0Pfrp9tL8e7lFzn2HGLspu+/3Tn3IwTzZAHgadYLdvT19cn7nrWjs7uz6bO5VM5b1NSNMZamTIYFza1ENpouLs++4ipREkQrRTqXIpXz8dIa7aukAB1ZsgQUJi2L7nmAdEtMJReg7AypoBGvlbM+ax4a59xfnMQ0pZD6FkznLKWRcejKo7uaEpk1YyE29dKLe1x3xdai6RqfK4c4SWLBJPab0bARJUjKwxSrhEfG8NMpsJZ9Q6Okwxrh3kNUxycR61CBlyRTzmHDEBNWdHVRzjXhPaX61Tu2CuLcwC9fbPJJD8Dtfcim3ZtkbLz0uXzQekZnrtV42lNhHLOqa2GdeClzFkzP7jK4OgnOGYczgJWk6GyFrPY5Plyi9OhuzmaUY62ZGYZ0/b/KOqo5n65jBa76+qN4mWDalyqtqFVq1MaK+OsWQjpIFBgkEUSavYK9oYZvaw2QgWjBlmrTrGpbrM3y1cknQKV8KvtOYsZKeEr40T178dJ5mlubsZUYO1kmPDqMGRpPCuDOIc6irMUPAuMbceHeE9cA8A+7ZN4F/w9O39U7vP5+if/syu/fmAnS1+dTXpzxPW+yVqI1l6O9qYm4sRJhVvGtwe+TOds6Zrh/ShQZ32Pv8WEe3beH16wv4BmPasqf9pXKJfrJ5VzA4gNTPO1f99DsVKJsauoW0loKw+OY2JA6e0VSE6yL7blaXM9k63rRWuGMwxarM+KV9ZFJO1EGpZLFNF5SK6qvUABPUbj1UXK+x0MnxjlUjnjxS66ri3JaxDlsGGNLVexkMVHlUglBVmslxlqJauGZeIrtt2DnAfg/sX63bDX0PBjUjh54Z1u2xTUFGbEYImPobm1LoGZtsp+tUS+bpQHtZq1Jci6Zpgy0T81E3Ln/AI8eO8Gr1tboSgvRuMN3YLVgHMRpjbWOjT8/xmXfPUBOe5DzkTgpSSulKI5PURqawF/cSmrTsoQJUy+boIR4sozXmp0GpJmqJOBQM2scxNO42IJtgG/GoovnEY+VKN+9j3QqxUOHTnDldZeQzqaJS2V03eILoPNpXOjhwgjx1LThjSo1IFhMyqM/7rfzLvh/YP0EcfHRg89rzbSdnQ9SFkFbl7i+1mwO6+zc1mndqjSoT845rLUY59Ba4WnNoeERdt57Pw8cOMbzV4RsaImoGEECYfWeYbJVi4oty/aMcv3nHuSp33iMbOBBykPV4z7RQhjFjJ8cw5ZrZC49A9WcwUVxYtTqnQysJR4pYEaLxGOlOn9Q5sr1A+KrGfDJzEIblUsxdctu4qOTeGkfE1mqx0ZxY2PJThRRM6WiesypAi+x9LHBRrFTonDGDBNGuCdoO89bwP/o3JKoMCmlX9eWbXXJ9TEYa/G1R9DYyyaP7+a76RYX+J6HwzFaKPDo8aMMjY9RCB3XLTNc2lWlEoKnHCbwWLJnhOd89A7EOtpGaviexrVkkgK2ddMEVxBGj5wkmqzgd7eQ27apXjKZNddh62Cwdbef8k5p+s4ibZ1KBbMO8T2i8SKjX7uDfGuWvcNTtC5ewMIzl2InqsRhAd2aR+frtcJpWREzrbpv4tgRGUTrI0SOnVf3aW7pj+cB+F+cnp4B3T/Ya/7ksn+/MpvKXxlo5xC0kBAClFL1ZTAWRZJUuPqSelVX+xRRRCbmxPgEB4dPcHJyAoUhsh6Xd4c8a1GFWuwSsmqyYRedS9FVMigE21If37SuPiSexFVoxdiRYapTZYhimp6zBa+7GRfWM9s5VBeXyGnMHsr9z+yQEqjFOOfQbVmG/vknuKMTqKWdPHLwBNffcDXdi7uwxRqBNZhqDVuuony/3kOuSxSbJCyJyjVxJsZf2vEwkOyNu2XeAv63j6/917Zn2kXEGeeMQhJwVeMIg01mHqxN6n/1tloYGwqlKiNTU5yYGGeiVMRZSyrQlGPFpraI3lWVZJODqzNW6iNkWjRobzr7nZkZTtCjPI/xYyNMjkzgqiGZLavIXbUJW41m5N7cKaZ49mqI/yLwcbUYWw7xF7dQuHMfEzfdQdCax0WGvNK40SKuqwpxDFqhs5lkd3AtTBjU1tabyRZEUR2ZVKrJJ7v1zNsBtm7a5OZd8H9d95PBQTF/dNnXmzzNU3zlsNboRk3NVwkH9aEjh2nP5fA9v66WEVKuhRSqZapRRBRFOOdIez6BVhQjy+p8lReuKgE2mQuZqXZM06Xk1I2+9S6F8jSjx4eZGhqHmkF35Wl/yVbAIsqba/Ue3/pgTltkzvdJ0dmFBjNVRrfliIYLnHzfd/ADj8DTWCy7MhHdDz7Kos5m6GpOOik2nvk1cTwtoCTOEceRlWJN4rM7Dvmru++vu5b5LPi/OgM9g6p3EOPr3FW5VNNCSTgoajozFKE5laVQLXGoMpI0PGYp3AXaJ6U11kQImkBrKrGlKx3x4uUFPBsTo9H68UaK2bXDBka04IxjaN8JCpMFlHOonE/XG56J15yZAdIpiqtzwNyIU+vq+TOrm+qk02qEmaqiUon66rH3fAM3XEC35Wlyii/nK3zijCrxfUfZ+Fg37f4KvFwm6ajUm8zOJot4nLWgheLxMZfOZZW5ZN2nRWTKzfeC/3tn11CiQZzScnFT0IyIsc65RMquXhvTCO2ZZiwW6yzGmenMd6w6yVS1RFoFBL4mto6MNvQuHiMjEaHRaG1xTv2Hvb8GAJVWhNWQ0cNDVMo1qMWQD+h667NIrUliMd2enb6/PI7+PNfyuWoEWiFeHXjG4cohphImSYqvOfaebxA+cJR0VwsZFIdNlX9qmuKyq67inoWH+Ifv388raxGL1q3Ay6frm9ldPQ9J9DjCSmjNySlVunjlyY5tm/7BgTxZrN+v3gXfstUCpFRwfkIEtY29trMmyWSanayUwhefyXKBA1PHUGjaUs317ZdJCea53cMsSIVUrEIrl8Tq2LpaVGKNbN19OZkhg46fHGfi5HhizqoR3qIWul//DFKrurCFaiKATsP6zdqMNG0CG7R6myzM8VR9Os8koum1OKHc59PEhSon/+7fqD5wmGxHCwJ4zvGPrZOkNy/jnKUruK1UYeDhRxg7/iCviCpsWL2SVFseG9f300mSqRf3H7e5JZ2e3HDRH4rIyJPJ+v3KAdiP2I9vudOflMoamd7q7KZd7VxFT41zliOTxzk8cZLmdAtd2TasjVHiKFuPi5tOsDZdoGRSeDK3PYeq0/AbFs9LKFvlYpmJk+NUihXEJItucpeuo+MV2/BasthyFVEqSTwaNGNXn3abTauvrwpzUeIqxboEdKFJuhi+xmvLUdl9jOFP7MCcGCfb2ZL0rxHGxXFrk2HLwoWcHB6mdHwEWd/Nv5uDPG9qkqhcxW/OTnda8BRTB05EeT/t156y7uNtGxd/YVo350l0fmUATC6huOHscGdG8osctvGzU9IU8JQmMoa9IwcZKo7SnmmlO9uBdRGihNgpFvkVLsqPUXUaZc20zEYjSHMWRCmUl3DyyoUSk6NTVEpVbDVMrF5XMy0vvormp25K9g+Xa8nFFsHVTFJm8RpU6zqwY4uNbULXsvWYz5LsM5a6ZUx5zjnnxv/tHpn8xt2iwphUSw7VoOMroV0ptkwpvrnzJ6xv6SC2jpPjY/xZfj2XNS/F5NPYMEJ5gsO5qf0n4myIHz517Tdbn3fR6wdsj34yud5fOQC3sz3xh5GvJN3QdxLmEqMcnvIoR1X2DO2jVC3RnMrTlevEEc/08R1cmBsi8Cyx8nAuiRcVapoZjQixMVQLJQoTRSpTRUw5xPMUXlOW/LVn0/z08/C7m7Gl6vQE3EzB2OJK4Rzqs5uW85311Bua01rA04iIk8PjMvGVO6X44CFULjBeLu3EOFFaIVppay2FWsTbpYuoOMbNY4eoxFV60kt5fftawpQmGY6xmBg7efAkeT/jR09d942WV279XRGx9bDFzQPw/481dBY3Lf4t9XKJwxNNsVZm98nHCOMQX2na0i11QcYkE4yMsDBdZWW2SjlypDyL6KRgbY0ljmJq5RrVSpWwUiEq15Lyn/JpPmsJmS3ryG5ZTWpxK64cYouVhLk8t9VSb1oKzti6NRW0B9qXxKo2gFevObrIYE4UkcMFqRTLFe+cJUd0ubSouWDydR431sRUwhqxgPI1HeksH67leTBuoyiGS1Q3cYO65WtXmSyZeLjgSXOK+Omb39vygkv+pA4+eTKC77QAoMuIh4jfcGtOErazVpqqqbHn5GOEcQ0lQtbPkvEyOGumyx2xE9ZlJwk8S6ViqBZLOCAKI6JqSFzvmxqrmJQc5fRCJoMmjtWa2HL5Oq58XhfVoQrReBmlJanTMWuNQ30zkrOgPYefUSgtxKGjOGUZPxEyNRJTqThKxmDz4GccuSi0C3GqpTO3u+WFFz4lDyP+jResir58x7W10clLzPGpnO5q7fKtvdD+Yl8mk88Q4Yic4eygGV9rqmJdZJ21YYwdqemMn/bk3JVH/RvOfXPunJVfcb8zPV75pATfaQFAEReDjZxz6emfOSEyMQ+fOGSrYVV59Y5FNsgwW+/YOvDFssgvY6wl25wFyWKMwRhT1+JT+IGmJil+eGwJ5ShIGCUpx0//5QSV4SqXP7uDbFuAjV19h5ybrt8pRRJ3iVApWo4frHLkkRqHd1WYGrFYA9KqcEs18SKFS4FLgc1pSaUD8r7uMDc9+Nvj/7rnX9822LsX2At8DAXOuPTBl37swXwut9IiViSZsKq42JXDSOnYqQCt/WxAbe3CMXXhuk+03HDuh0TkhOsZ0Az02Ccz+OA0YEz00ady1zzl7s5c1zlIZBGllMC+kWOUpcTU1BRaPLRSLGxagK8SMNYTT7La8sJFB0npGCeJdZpeV6ASWTSDkNaWH51o4dZjedrSAioxutWKo3N5inXn51m8Lk1TqybIJC44rlrKBcP4CcOJ/TWGD4YMH4kwxtGxxKN1naLpbJ94ucdkmyJOJ0DFgbXJgJGympTLUD0yeby5qL/aPBZ/6qm/t/m+AXr0Wdecc+Gi9rbblChsbJPnrhRoIfIgzPoF1ZH/afOWtTelbzjvuyJyBGaEm/g1OL9SAA70DOjewV7znmt2/OuCpoU3IlGsRXnDUxOMyVh4wTOW7P33z+za6HkKTwmLmhfhicZJA4BCq454weJDeJ6bnpJr8JyUTi6mrQsOWRRf2dfOsVKO5lSyMdL3feLQUa0axINURuGn6wQ7qyAWwipUa5ZURrFsGSw/A3IbPCp5KKQUx5s8ykGi8+xk7h4646wz4qzn+TpnM3gHShWvEPc/91ln/e0j37m7q31o8sVmaOosG5kloIyqhg977bkj+swlR1uuO+c2CeQQ9RHkXxerd9p1Qqx1OyJrbtRixbjY1Az63GuWDrQtCf5IK71fRNIi4lRjiUbdETsRrCjQGqXMdLursQlT6sLfWsA5IfCEng0Fbj6keHQ0S9rT+AbSgSKX0fWxScFFYE3CanWiaW6ybFgVsW5VTPtiCH1hquyIrGZkmU85pRMCzSm934TXIKIRbcPITerYqKWS6Qxb/+Zfbn9g2fqLN78B+ACQzC07Hidn0Adqa98OtZWdVvp7zZOD5fffP79aQurWhAdYLkY3jxVHqlqLLoWhal3uRz1/ct4Ht/WedUKEg54KEPHcHFU/BxpH2WkqzkdLQstSoqa7HjMyvRpfaxCPtBaeu7bAM9dNsqQlRKkkkw6NJowUkREcmiDl0dUO562pcP1FRZ5yfpmlrRFUDKZmyYSWiRaPiZyHU2BSYDIOm3XYnCPOOkzGJRN59XE/ZZxnMW44NRXFi1te/5ndD7xZgDtf/XG/z6CcRTl6tOvb4bmBAe36+lQ/2G392+LG6Oqv2zktYsB++u2fb7355kVt3deMFQqsuSb37d53nf9sEzn5/fO/+Plc0PLCyFZMd77DC7Q3U7IRR9VqnrN4hLObpqg6D6Wox4AzFrBxW3k6oTIowQsEh2Ks5jEepilbj9gKgUA+A20tjuasQZQDFFHCkcB5gtWKky0+t17QTJxS2JLDGxLUiKCLgsRARog7IVxiCVsMVFxd3Bycdc5pbTEmXpHOXHT9sjUPNDRb+A07v/IseFPPJmEQVMr8/YnR0WvbFzVz7jVLvmrfgYiIe83Z/3wzuBc5ZyWyMSntTXP2Gh73oUKOs5qKDX584kobiYiohF9Tr+2pOihNnMSHHTlLR3MyKJR8zYhZukhjJOnpau0wIogBP23ZtzJFfFDIPgB6v0KNgY5nmPgiJPFnq6Z8jmLsiggbOKg5rDhxcYSXzaWGK7W/VPCcXT27HL+B57SIKProU/2q377nmd//xNINbU978Xu3bBGRUYC3bxloqYl7GOV1+1q5zmyrmub0JTUbIiv8zoohVuWr1JyHriNApD4UpOe6ZRoAna77JcmDJJ2JWZSqpAfsVGItdZC8Yw/ZPA8M5fEekSRxTynwXD3xkVkL2gXtFF5NiJYLx58fErbGEDoQ5yLn8B3hMxeu2LSitfWxhAkkdh6AvypzHCiimmkTkXFI6PqDg73mzZd8+S88su+qxsW4O9fupbxUfVtlwsMLrdCdifjddcMoBOcSreiGtXP1hEQaSuOqPkgkicWTxqYilZRRGsBNhshV0jnxHOPlNLuPN3HsRArPgKSThdViE7ApJQ2xVKeUckpEDFaMshJUNfFi4dhLqhjPYo3D4kw6m9Ub/NTLrl604rM7duzwtv0SthPNJyH/wYlDi4iMu0Q9koHBHutwkl6de38lKhxRytOTYclOK927xmiu5VjJ4+aj7aQ8UOKwbtaguKvz96bXsM66zczPnHUJq8U4nHEoZ9EqolwT7tnfyg/vbefIiTS+B6RImBI2eRytlI1CYyYnajI1GatiwerJQqTK5UgInQ0zFu+4JX+rIgymH9pZpYiMW8Fv6Dnt1jTMbi0J4np7BtXffOlZ4+mcvMlXWmpxZAth2SX7z+y0QkLas9wznOKbB1pBKdKewdYldqm30hprGhqF4ulxTuOwscWZpL+sJUZJTKGiuO9QK9/ftZCHjzWjREjpunBgHbBaK6omMifGSqooTrvuaDi30d2e2hD/qJwvPDRRKRLFolxsXagMqd2CK4FTyfOOnOU3+TwpqkoNV/z2a77yZ6aY6i9Hxbgj26xzQVYazGCpu+NarFneClcvLbM0VcSvA8ag6rK8M25WlCThoKrX4ZQicj4j1QwHJ/IcmcxQizxSfkMAa0bwXIvCYNxooeicF6i21Xrvhm1df7f5GQu+kW7yTprYEFWc/6MPPnLpgV9M/n2G3AWpACtpUUdeHhG1WVxkTSqT1RflWl568YLFn3PJng4zD8DT8Hn2MKC+6t1o/nDr4Efjgvf6yFRNW7ZVcn5aWWemN5h7WoiMIvAD1rRrVuVLdPglmoOQtLZoXEIuFYV1QuQUZRcwEQUMVbIMlzIUwxSCItAOJTO9Z6eSUVARqEShOTFW0Ok2j01P7frYVa9a9S4RGTvlvXUAn3/nnYuKD0Z3d7e3LZDAcPBloZgOS1SzrsVP2VesOuOcVCq1az4JOe2fa5+I12/fff03/7Q4HP9lHBua0pk4H2Q8V9fITQrR9bhPB2RSWXK+RyAxaR0TaJuIHIkitorQaGrWI7aqXpdy+Jp6QqFmJNsQPK0JbeROTkzZamj1gjMyYxf1Lnnzhq0LPo+FHX07vK3bt87oLwsMPP/BoHfwrPAfnnfr+5a3LX5bOVeKH3t51fPTmKpotdZP/ewFqzdcLdQLm/Mx4Gl7HGx3Lu5Tf/7N5/xV97rMjem8d7waG2+sPOkszmjRc9jPuJhSZYKJ8iRTtZipMMVE1MRoJcdIOcNUmKZmEoHKlDKklMGrE6mta4wCKLQoQhO7oxNj8aPHTopJoTde0/nd3/3IeZdvuGrB53vsgHbOybb+bfGcPq2DXUPDtq+vT0la7nRlw9jKUEyTZaoSubwfyOVdC98vInbgyXUtfiMBWM9n+20PA/od//yMgYt/Z9FFuU4+ZbRhslzVk5UixjqjEr+JtfU9H2HIRKXAaHmMyfIEYVxFiNFi8VTCQBHUNIPaAbE1lMOaGy5OmX0jQ2bv8SGpOOet2NJ65NrXrfrd5/Wf+QwReWigx+lB/hPV+e5h1b99u8sc9k3UDpNXGlcphlEqn/fODrKfW93S8TXnnOr9DYv9nowu+AkTExR84m0/vfLYnvE/LkxWr0+5vNIIvlbG0wotGieJf7VYMfXsV6tEwMhTGiWKROXMOmtxsbUuNobIGK3Ep6k1S8cK//iZVyz45AXPX/wxETnBzK6N/yRmm9mI8/FX3HvTWA/PPrlgQrWn29Ul+eabr1264rcFSnXJ3vlOyJPtOOekV3rVIING+fDlv7zrgv33jLx4crLaY6veYhVqvHpMqBVY50wjW7bItLagSyqLShAxMaT8FJlsCr/F1NqXZH561rYlN5337EVfFZGTAAM9TvcO/ucWq1HLfNXnb165LN30Xlnd/PxqrkJHpEqXLFj4vsu6F/+ViERPdkbzbzQAG6evz6n+/u1AwhhxznUM/v1dTx8+OHXNxPHa+rjizgirpintZQIbu8TZiqCUQolGaXAqRpSbzLUHY83d6QcWrM/dcd41S25auKF5d1xNHmegZ0D3/Hf5eM5JH0jbnXd8Jwz0FhF76+Z8167rVq34gojsPrXmOQ/AXxMg7u4flEFmWCVBVlMrxe07v/zY4qljpTVHH5nw0tlUS7ZJd6pAm7joTja3Z8pda7OTK89dsat7JUXxpDhL5lv6+nbo7bOz2/+ZlW4DKiJSnQ4fBgb0QM+vF7F0/pzi/gZ6nO7h/69Qd58a6HHa9Tn1v/jpUAPOaeecmr9Cv6YW8D9MnZ1j+3Zk0yaEQSD5DzT2afQkP+upD3b/b1qmRiw4b+3mz/yZP/Nn/syf+TN/5s/8mT/zZ/7Mn/kzf+bP/Jk/82f+zJ/5M3/mz/yZP/Nn/vymnP8P4sfppcT63MgAAAAASUVORK5CYII=", yf = "" + new URL("NotoColorEmoji-nature-Rpfd13Si.woff2", import.meta.url).href, xf = "" + new URL("NotoColorEmoji-objects-EKxheXEn.woff2", import.meta.url).href, wf = { sans: 'Manrope, "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", "Avenir Next", "Segoe UI", sans-serif', mono: '"IBM Plex Mono", "SFMono-Regular", "SF Mono", Menlo, Consolas, monospace' }, kf = { eyebrow: { size: "0.6875rem", weight: 650, lineHeight: "1.1", tracking: "0.12em" }, sectionLabel: { size: "0.6875rem", weight: 650, lineHeight: "1.1", tracking: "0.12em" }, pageTitle: { size: "1.375rem", weight: 650, lineHeight: "1.2", tracking: "-0.02em" }, subtitle: { size: "0.8125rem", weight: 450, lineHeight: "1.45", tracking: "0" }, body: { size: "0.9375rem", weight: 400, lineHeight: "1.6", tracking: "0" }, input: { size: "0.875rem", weight: 450, lineHeight: "1.5", tracking: "0" }, mono: { size: "0.75rem", weight: 600, lineHeight: "1.4", tracking: "0" }, scoreValue: { size: "1.25rem", weight: 600, lineHeight: "1", tracking: "-0.02em" }, scoreLabel: { size: "0.625rem", weight: 650, lineHeight: "1", tracking: "0.08em" }, footer: { size: "0.6875rem", weight: 450, lineHeight: "1.4", tracking: "0" } }, Sf = { card: "12px", input: "10px", panel: "16px", pill: "999px" }, jf = { duration: { fast: "120ms", mid: "200ms", slow: "420ms" }, easing: { standard: "cubic-bezier(.2, .8, .2, 1)", entrance: "cubic-bezier(.22, .8, .2, 1)" } }, Ef = { light: { washLow: "#FCEFD4", washHigh: "#F5B3A6", lineLow: "#E8A13C", lineHigh: "#D64540", safe: "#0E9384" }, dark: { washLow: "#4A3A1E", washHigh: "#4E2A26", lineLow: "#E0A24A", lineHigh: "#E8756B", safe: "#5FD6C6" } }, Nf = { light: { colorScheme: "light", canvas: "#FAF3F8", card: "#FFFFFF", surface: "rgba(255, 255, 255, 0.92)", surface2: "rgba(255, 255, 255, 0.80)", scrim: "radial-gradient(120% 90% at 50% 30%, rgba(250, 243, 248, 0.78), rgba(250, 243, 248, 0.30) 82%)", ink: "#231A21", muted: "#6B5F68", faint: "#A395A0", line: "#F0DFEA", lineStrong: "#E2C8D8", brand: "#E562A8", brandBright: "#EF7CB8", brandWash: "#FBE7F2", safe: "#0E9384", safeWash: "#D7F0EB", warning: "#81520C", warningWash: "#FCEFD4", riskInk: "#D64540", riskWash: "#F8DDD7", focus: "#1B6ED1", link: "#0E9384", mint: "#AFDEDD", shadowColor: "rgba(65, 45, 61, 0.14)", shadowCard: "0 1px 2px rgba(16, 24, 40, 0.04)", shadowRaised: "0 22px 62px rgba(69, 37, 57, 0.12)", sidebarBg: "rgba(255, 255, 255, 0.92)", inputBg: "rgba(255, 255, 255, 0.96)", popoverBg: "rgba(255, 255, 255, 0.98)", optionHover: "rgba(229, 98, 168, 0.16)", btnBg: "rgba(229, 98, 168, 0.10)", btnHoverBg: "rgba(229, 98, 168, 0.20)", btnHoverBorder: "rgba(229, 98, 168, 0.50)", pillBg: "rgba(255, 255, 255, 0.70)", pillSelected: "linear-gradient(135deg, rgba(229, 98, 168, 0.22), rgba(14, 147, 132, 0.16))", pillSelectedBorder: "rgba(229, 98, 168, 0.55)", scrollThumb: "rgba(229, 98, 168, 0.50)", scrollThumb2: "rgba(229, 98, 168, 0.42)", scrollThumbHover: "rgba(229, 98, 168, 0.66)" }, dark: { colorScheme: "dark", canvas: "#151116", card: "#211A22", surface: "rgba(33, 26, 34, 0.92)", surface2: "rgba(33, 26, 34, 0.80)", scrim: "radial-gradient(120% 90% at 50% 30%, rgba(18, 13, 20, 0.50), rgba(18, 13, 20, 0.10) 82%)", ink: "#F9F5F7", muted: "#B9ADB5", faint: "#8E8089", line: "rgba(255, 231, 242, 0.15)", lineStrong: "rgba(255, 231, 242, 0.26)", brand: "#F07EBB", brandBright: "#F79BCB", brandWash: "#4D2034", safe: "#5FD6C6", safeWash: "#173B37", warning: "#F0BE6D", warningWash: "#422F17", riskInk: "#FF9499", riskWash: "#4E2428", focus: "#6CAEFF", link: "#7FD8CA", mint: "#AFDEDD", shadowColor: "rgba(0, 0, 0, 0.50)", shadowCard: "0 1px 2px rgba(0, 0, 0, 0.30)", shadowRaised: "0 24px 70px rgba(0, 0, 0, 0.32)", sidebarBg: "rgba(21, 17, 22, 0.93)", inputBg: "rgba(20, 16, 24, 0.80)", popoverBg: "rgba(24, 18, 28, 0.97)", optionHover: "rgba(240, 126, 187, 0.22)", btnBg: "rgba(240, 126, 187, 0.16)", btnHoverBg: "rgba(240, 126, 187, 0.28)", btnHoverBorder: "rgba(240, 126, 187, 0.55)", pillBg: "rgba(33, 26, 34, 0.66)", pillSelected: "linear-gradient(135deg, rgba(240, 126, 187, 0.30), rgba(95, 214, 198, 0.20))", pillSelectedBorder: "rgba(240, 126, 187, 0.60)", scrollThumb: "rgba(240, 126, 187, 0.50)", scrollThumb2: "rgba(240, 126, 187, 0.42)", scrollThumbHover: "rgba(240, 126, 187, 0.66)" } }, be = {
  fonts: wf,
  type: kf,
  radii: Sf,
  motion: jf,
  spanRamp: Ef,
  palette: Nf
};
function Ga(u) {
  const a = be.palette[u], c = be.spanRamp[u];
  return {
    "--canvas": a.canvas,
    "--surface": a.surface,
    "--surface-solid": a.card,
    "--ink": a.ink,
    "--muted": a.muted,
    "--faint": a.faint,
    "--line": a.line,
    "--line-strong": a.lineStrong,
    "--brand": a.brand,
    "--brand-bright": a.brandBright,
    "--brand-wash": a.brandWash,
    "--safe": a.safe,
    "--safe-wash": a.safeWash,
    "--warning": a.warning,
    "--warning-wash": a.warningWash,
    "--risk-ink": a.riskInk,
    "--risk-wash": a.riskWash,
    "--focus": a.focus,
    "--shadow": a.shadowRaised,
    "--shadow-whisper": a.shadowCard,
    "--span-wash-low": c.washLow,
    "--span-wash-high": c.washHigh,
    "--span-line-low": c.lineLow,
    "--span-line-high": c.lineHigh,
    "--span-safe": c.safe
  };
}
function zf() {
  const u = {};
  for (const [a, c] of Object.entries(be.type))
    u[`--text-${a}-size`] = c.size, u[`--text-${a}-weight`] = String(c.weight), u[`--text-${a}-line`] = c.lineHeight, u[`--text-${a}-tracking`] = c.tracking;
  return u;
}
function Cf() {
  return {
    "--font-sans": be.fonts.sans,
    "--font-mono": be.fonts.mono,
    "--radius-card": be.radii.card,
    "--radius-input": be.radii.input,
    "--radius-panel": be.radii.panel,
    "--radius-pill": be.radii.pill,
    "--dur-fast": be.motion.duration.fast,
    "--dur-mid": be.motion.duration.mid,
    "--dur-slow": be.motion.duration.slow,
    "--ease-standard": be.motion.easing.standard,
    "--ease-entrance": be.motion.easing.entrance,
    ...zf()
  };
}
function Ya(u, a) {
  const c = Object.entries(a).map(([y, x]) => `  ${y}: ${x};`).join(`
`);
  return `${u} {
${c}
}`;
}
const Rf = [
  Ya(".sirin-component-root", { ...Cf(), ...Ga("light") }),
  Ya(".sirin-workspace[data-theme='dark']", Ga("dark"))
].join(`

`), rc = "recordedResultVerified", Pf = {
  recordedResultVerified: "Recorded result · verified — detection not live"
};
let _a = !1;
function Tf(u) {
  if (u.querySelector(":scope > style[data-sirin-tokens]")) return;
  const a = document.createElement("style");
  a.setAttribute("data-sirin-tokens", ""), a.textContent = Rf, u.prepend(a);
}
function Lf() {
  if (_a || typeof FontFace > "u") return;
  _a = !0;
  const u = [
    new FontFace("Noto Color Emoji", `url(${xf})`, { style: "normal", weight: "400", unicodeRange: "U+1F9EA" }),
    new FontFace("Noto Color Emoji", `url(${yf})`, { style: "normal", weight: "400", unicodeRange: "U+1F984" })
  ];
  for (const a of u)
    document.fonts.add(a), a.load().catch(() => document.fonts.delete(a));
}
const ba = {
  analyze: {
    task: "faithfulness",
    mode: "generate",
    exampleId: null,
    context: "",
    question: "",
    answer: "",
    prompt: "",
    sourceRunId: null
  }
}, Of = { theme: "light", motion: "subtle" }, lc = 240, ic = 180, Ff = 400, $a = /* @__PURE__ */ new Set(), Mf = /* @__PURE__ */ new Set(["consent_required", "busy", "empty_answer", "generation_unavailable", "judge_no_aligned_annotation"]), Ul = /* @__PURE__ */ new Map();
function If(u) {
  return u ? { analyze: { ...ba.analyze, ...u.analyze, prompt: u.analyze.prompt ?? "", sourceRunId: u.analyze.sourceRunId ?? null }, quickPrompt: u.quickPrompt ?? "" } : { analyze: { ...ba.analyze }, quickPrompt: "" };
}
function ec() {
  var c, y, x, E;
  const u = (c = globalThis.sessionStorage) == null ? void 0 : c.getItem("sirin.client.id");
  if (u) return u;
  const a = ((x = (y = globalThis.crypto) == null ? void 0 : y.randomUUID) == null ? void 0 : x.call(y)) ?? `client-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  return (E = globalThis.sessionStorage) == null || E.setItem("sirin.client.id", a), a;
}
function nc() {
  var u, a;
  return ((a = (u = globalThis.crypto) == null ? void 0 : u.randomUUID) == null ? void 0 : a.call(u)) ?? `action-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}
function Ie(u, a = !0) {
  return typeof u == "boolean" ? u : u && typeof u == "object" ? u.enabled : a;
}
function tc(u) {
  return u && typeof u == "object" ? u.reason ?? void 0 : void 0;
}
function kn(u) {
  return u ? u.replaceAll("_", " ").replaceAll("-", " ").replace(/\b\w/g, (a) => a.toUpperCase()) : "Unavailable";
}
function on(u) {
  return typeof u == "number" && Number.isFinite(u) ? u : null;
}
function oc(u) {
  return Math.min(1, Math.max(0, u));
}
function sc(u) {
  return u >= 0.995 ? "1.0" : u.toFixed(2).replace(/^0+/, "");
}
function Ao(u, a, c) {
  return `color-mix(in srgb, var(${a}) ${Math.round(oc(c) * 100)}%, var(${u}))`;
}
function ql(u, a, c) {
  return a === !0 || u !== null && c !== null && u >= c;
}
function uc(u, a) {
  const c = a ?? 0;
  return oc((u - c) / Math.max(1 - c, 1e-6));
}
function zr(u, a) {
  const c = on(u);
  return c === null ? "No score" : ["calibrated_probability", "calibratedProbability", "categorical_probabilities", "categoricalProbabilities"].includes(a ?? "") ? `${Math.round(c * 100)}%` : c.toFixed(c < 10 ? 2 : 1);
}
function Wf(u, a) {
  const c = a == null ? void 0 : a.trim();
  return c || (["calibrated_probability", "calibratedProbability"].includes(u ?? "") ? "probability" : ["relative_within_answer", "relativeWithinAnswer"].includes(u ?? "") ? "relative score" : ["thresholded_raw_score", "thresholdedRawScore"].includes(u ?? "") ? "raw score" : ["categorical_probabilities", "categoricalProbabilities"].includes(u ?? "") ? "class confidence" : ["span_agreement", "spanAgreement"].includes(u ?? "") ? "judge agreement" : u === "verdict" ? "verdict score" : null);
}
function Al(u) {
  if (typeof u != "string") return "neutral";
  const a = u.trim().toLowerCase().replaceAll("_", " ").replaceAll("-", " ");
  return ["risk", "suspect", "unsupported", "hallucinated", "hallucination", "failed", "error", "unanswerable", "unsafe"].includes(a) ? "risk" : ["safe", "supported", "faithful", "answerable", "passed", "grounded", "healthy"].includes(a) ? "safe" : "neutral";
}
function Hl(u, a, c) {
  const y = (u == null ? void 0 : u[a]) ?? (u == null ? void 0 : u[c]);
  return y == null || y === "" ? "Not configured" : String(y);
}
function ac({ status: u }) {
  return /* @__PURE__ */ s.jsx("span", { className: `status-dot ${Al(u)}`, "aria-hidden": "true" });
}
function wn({ name: u }) {
  const a = {
    analyze: /* @__PURE__ */ s.jsxs(s.Fragment, { children: [
      /* @__PURE__ */ s.jsx("path", { d: "M4 17.5 9 12l3 3 7-8" }),
      /* @__PURE__ */ s.jsx("path", { d: "M15 7h4v4" })
    ] }),
    runs: /* @__PURE__ */ s.jsxs(s.Fragment, { children: [
      /* @__PURE__ */ s.jsx("path", { d: "M6 5h12M6 12h12M6 19h12" }),
      /* @__PURE__ */ s.jsx("path", { d: "M3 5h.01M3 12h.01M3 19h.01" })
    ] }),
    diagnostics: /* @__PURE__ */ s.jsx(s.Fragment, { children: /* @__PURE__ */ s.jsx("path", { d: "M4 14h3l2-7 4 11 2-7h5" }) }),
    arrow: /* @__PURE__ */ s.jsx(s.Fragment, { children: /* @__PURE__ */ s.jsx("path", { d: "m9 18 6-6-6-6" }) }),
    spark: /* @__PURE__ */ s.jsxs(s.Fragment, { children: [
      /* @__PURE__ */ s.jsx("path", { d: "m12 3 1.6 4.4L18 9l-4.4 1.6L12 15l-1.6-4.4L6 9l4.4-1.6Z" }),
      /* @__PURE__ */ s.jsx("path", { d: "m18 15 .7 2.3L21 18l-2.3.7L18 21l-.7-2.3L15 18l2.3-.7Z" })
    ] }),
    download: /* @__PURE__ */ s.jsxs(s.Fragment, { children: [
      /* @__PURE__ */ s.jsx("path", { d: "M12 3v12m-5-5 5 5 5-5" }),
      /* @__PURE__ */ s.jsx("path", { d: "M5 21h14" })
    ] }),
    upload: /* @__PURE__ */ s.jsxs(s.Fragment, { children: [
      /* @__PURE__ */ s.jsx("path", { d: "M12 21V9m-5 5 5-5 5 5" }),
      /* @__PURE__ */ s.jsx("path", { d: "M5 3h14" })
    ] })
  };
  return /* @__PURE__ */ s.jsx("svg", { className: "icon", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "1.8", strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": "true", children: a[u] });
}
function Df({
  workspace: u,
  onWorkspace: a,
  setup: c,
  title: y,
  subtitle: x
}) {
  const [E, L] = ge.useState(!1), T = ge.useId();
  return ge.useEffect(() => {
    if (!E) return;
    const R = (w) => {
      w.key === "Escape" && L(!1);
    };
    return globalThis.addEventListener("keydown", R), () => globalThis.removeEventListener("keydown", R);
  }, [E]), /* @__PURE__ */ s.jsxs(s.Fragment, { children: [
    /* @__PURE__ */ s.jsxs("header", { className: "shell-header", children: [
      /* @__PURE__ */ s.jsxs("button", { className: "brand", type: "button", onClick: () => a("analyze"), "aria-label": "SIRIN Analyze home", children: [
        /* @__PURE__ */ s.jsx("img", { src: gf, alt: "" }),
        /* @__PURE__ */ s.jsxs("span", { children: [
          /* @__PURE__ */ s.jsx("b", { children: "SIRIN" }),
          /* @__PURE__ */ s.jsx("small", { children: "Honesty, made visible." })
        ] })
      ] }),
      /* @__PURE__ */ s.jsx("nav", { className: "workspace-tabs", "aria-label": "Workspace", children: ["analyze", "runs", "diagnostics"].map((R) => /* @__PURE__ */ s.jsxs("button", { type: "button", "data-workspace-tab": R, className: u === R ? "active" : "", "aria-current": u === R ? "page" : void 0, onClick: () => a(R), children: [
        /* @__PURE__ */ s.jsx(wn, { name: R }),
        kn(R)
      ] }, R)) }),
      /* @__PURE__ */ s.jsxs("button", { className: "setup-chip", type: "button", onClick: () => L((R) => !R), "aria-expanded": E, "aria-controls": T, children: [
        /* @__PURE__ */ s.jsxs("span", { className: "setup-summary", children: [
          /* @__PURE__ */ s.jsx("small", { children: "Detector" }),
          /* @__PURE__ */ s.jsx("b", { children: Hl(c, "detectorPreset", "detectorLabel") })
        ] }),
        /* @__PURE__ */ s.jsx(wn, { name: "arrow" })
      ] })
    ] }),
    E && /* @__PURE__ */ s.jsxs("div", { className: "setup-popover", id: T, role: "region", "aria-label": "Active setup", children: [
      /* @__PURE__ */ s.jsx("p", { className: "eyebrow", children: "Active setup" }),
      /* @__PURE__ */ s.jsxs("dl", { children: [
        /* @__PURE__ */ s.jsxs("div", { children: [
          /* @__PURE__ */ s.jsx("dt", { children: "Detector" }),
          /* @__PURE__ */ s.jsx("dd", { children: Hl(c, "detectorPreset", "detectorLabel") })
        ] }),
        /* @__PURE__ */ s.jsxs("div", { children: [
          /* @__PURE__ */ s.jsx("dt", { children: "Generator" }),
          /* @__PURE__ */ s.jsx("dd", { children: (c == null ? void 0 : c.providerLabel) ?? (c == null ? void 0 : c.modelId) ?? Hl(c, "modelLabel", "model") })
        ] }),
        /* @__PURE__ */ s.jsxs("div", { children: [
          /* @__PURE__ */ s.jsx("dt", { children: "Device" }),
          /* @__PURE__ */ s.jsx("dd", { children: (c == null ? void 0 : c.device) ?? "Automatic" })
        ] }),
        (c == null ? void 0 : c.layer) !== void 0 && c.layer !== null && /* @__PURE__ */ s.jsxs("div", { children: [
          /* @__PURE__ */ s.jsx("dt", { children: "Layer" }),
          /* @__PURE__ */ s.jsx("dd", { children: c.layer })
        ] }),
        (c == null ? void 0 : c.threshold) !== void 0 && c.threshold !== null && /* @__PURE__ */ s.jsxs("div", { children: [
          /* @__PURE__ */ s.jsx("dt", { children: "Threshold" }),
          /* @__PURE__ */ s.jsx("dd", { children: c.threshold })
        ] })
      ] })
    ] }),
    /* @__PURE__ */ s.jsxs("section", { className: "page-head", children: [
      /* @__PURE__ */ s.jsx("p", { className: "eyebrow", children: u === "analyze" ? "Evidence workspace" : kn(u) }),
      /* @__PURE__ */ s.jsx("h1", { children: y ?? (u === "analyze" ? "See where an answer leaves the evidence." : u === "runs" ? "Every result, with its receipts." : "Know what SIRIN is running.") }),
      /* @__PURE__ */ s.jsx("p", { children: x ?? (u === "analyze" ? "Generate or supply an answer. SIRIN checks it against context and makes uncertainty legible." : u === "runs" ? "Review immutable outcomes and carry portable records between sessions." : "Inspect the active runtime without exposing sensitive internals.") })
    ] })
  ] });
}
function pt({ label: u, hint: a, children: c }) {
  return /* @__PURE__ */ s.jsxs("label", { className: "field", children: [
    /* @__PURE__ */ s.jsxs("span", { children: [
      u,
      a && /* @__PURE__ */ s.jsx("small", { children: a })
    ] }),
    c
  ] });
}
function Bo({ value: u, onChange: a, ariaLabel: c, children: y }) {
  return /* @__PURE__ */ s.jsxs("span", { className: "select-wrap", children: [
    /* @__PURE__ */ s.jsx("select", { value: u, "aria-label": c, onChange: a, children: y }),
    /* @__PURE__ */ s.jsx("svg", { className: "select-chevron", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "1.8", strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": "true", children: /* @__PURE__ */ s.jsx("path", { d: "m6 9 6 6 6-6" }) })
  ] });
}
function Vf({ examples: u, selected: a, onSelect: c }) {
  return u.length ? /* @__PURE__ */ s.jsxs("div", { className: "examples", children: [
    /* @__PURE__ */ s.jsx("span", { children: "Try an example" }),
    /* @__PURE__ */ s.jsx("div", { className: "example-list", children: u.map((y) => /* @__PURE__ */ s.jsx("button", { type: "button", disabled: !!y.disabledReason, title: y.disabledReason ?? y.description, className: a === y.id ? "selected" : "", onClick: () => c(y), children: y.label }, y.id)) })
  ] }) : null;
}
function Uf(u, a) {
  const c = u == null ? void 0 : u.status, y = u != null && u.runId ? a.find((E) => E.id === u.runId) : void 0, x = `${(y == null ? void 0 : y.origin) ?? ""} ${(y == null ? void 0 : y.mode) ?? ""} ${(y == null ? void 0 : y.task) ?? ""}`;
  return c === "running" ? /answerability/i.test(x) ? { label: "Checking answerability…", detail: "Judging whether the question is answerable from the context." } : /generat|quickPrompt/i.test(x) ? { label: "Generating…", detail: "The model is drafting an answer, then SIRIN scores it against the context." } : { label: "Scoring…", detail: "Running the detector over the answer." } : c === "queued" ? { label: "Queued…", detail: "Waiting for the runtime to pick up this run." } : { label: "Working…", detail: "The result will appear here when the operation finishes." };
}
function Zo({ activity: u, runs: a = [] }) {
  const { label: c, detail: y } = Uf(u, a);
  return /* @__PURE__ */ s.jsxs("section", { className: "result-card activity-card", "aria-live": "polite", "aria-busy": "true", children: [
    /* @__PURE__ */ s.jsxs("div", { className: "activity-status", children: [
      /* @__PURE__ */ s.jsx("p", { className: "eyebrow", children: "Working" }),
      /* @__PURE__ */ s.jsx("h2", { children: c }),
      /* @__PURE__ */ s.jsx("p", { children: y })
    ] }),
    /* @__PURE__ */ s.jsxs("div", { className: "skeleton-lines", "aria-hidden": "true", children: [
      /* @__PURE__ */ s.jsx("i", {}),
      /* @__PURE__ */ s.jsx("i", {}),
      /* @__PURE__ */ s.jsx("i", {}),
      /* @__PURE__ */ s.jsx("i", {})
    ] })
  ] });
}
function Hf({ answer: u, onComplete: a }) {
  const c = ge.useRef(a);
  c.current = a;
  const [y, x] = ge.useState("");
  return ge.useEffect(() => {
    x("");
    const E = u.match(/\S+\s*/g) ?? [u];
    let L = 0;
    const T = globalThis.setInterval(() => {
      L += 1, x(E.slice(0, L).join("")), L >= E.length && (globalThis.clearInterval(T), c.current());
    }, Math.max(24, Math.min(70, 900 / Math.max(E.length, 1))));
    return () => globalThis.clearInterval(T);
  }, [u]), /* @__PURE__ */ s.jsxs("p", { className: "answer-copy", children: [
    y,
    /* @__PURE__ */ s.jsx("span", { className: y.length < u.length ? "caret" : "caret hidden", "aria-hidden": "true" })
  ] });
}
function qf({ answer: u, result: a }) {
  var L;
  if (!((L = a.segments) != null && L.length)) return /* @__PURE__ */ s.jsx("p", { className: "answer-copy", children: u || "No answer was returned." });
  const c = on(a.threshold), y = a.segments.map((T) => {
    const R = on(T.score);
    return ql(R, T.verdict, c) ? R ?? 1 : -1;
  }), x = y.indexOf(Math.max(...y));
  let E = 0;
  return /* @__PURE__ */ s.jsx("p", { className: "answer-copy segmented", children: a.segments.map((T, R) => {
    const w = on(T.score), B = ql(w, T.verdict, c), A = T.startCodePoint !== void 0 ? `characters ${T.startCodePoint}–${T.endCodePoint}` : "text segment", Z = [A, w !== null ? `score ${w.toFixed(2)}` : null, c !== null ? `τ ${c.toFixed(3)}` : null, "probe confidence, not calibrated"].filter(Boolean).join(" · ");
    if (B) {
      const oe = w !== null ? uc(w, c) : 1, ce = Ao("--span-line-low", "--span-line-high", oe), K = { "--seg-wash": Ao("--span-wash-low", "--span-wash-high", oe), "--seg-line": ce, borderBottomWidth: oe >= 0.5 ? "3px" : "2px", "--d": `${lc + E * ic}ms` }, V = R === x ? "evidence graded is-peak" : "evidence graded";
      return E += 1, /* @__PURE__ */ s.jsxs("span", { className: V, style: K, tabIndex: 0, "aria-label": `${T.text}, ${Z}`, title: Z, children: [
        T.text,
        w !== null && /* @__PURE__ */ s.jsx("sup", { className: "evidence-badge", children: sc(w) })
      ] }, `${A}-${R}`);
    }
    return w !== null ? /* @__PURE__ */ s.jsx("span", { className: "evidence below", title: Z, children: T.text }, `${A}-${R}`) : /* @__PURE__ */ s.jsx("span", { className: "evidence", children: T.text }, `${A}-${R}`);
  }) });
}
function Af({ result: u }) {
  const a = on(u.threshold), c = (u.segments ?? []).filter((T) => ql(on(T.score), T.verdict, a)), y = c.map((T) => on(T.score)).filter((T) => T !== null), x = y.length ? Math.max(...y) : null, E = c.length ? Ao("--span-line-low", "--span-line-high", x !== null ? uc(x, a) : 1) : "var(--span-safe)", L = c.length ? `${c.length} suspect ${c.length === 1 ? "span" : "spans"}${x !== null ? ` · max risk ${x.toFixed(2)}` : ""}` : "No spans above threshold";
  return /* @__PURE__ */ s.jsxs("div", { className: "span-footer", children: [
    /* @__PURE__ */ s.jsxs("div", { className: "span-verdict", children: [
      /* @__PURE__ */ s.jsx("span", { className: "span-verdict-dot", style: { background: E }, "aria-hidden": "true" }),
      L
    ] }),
    /* @__PURE__ */ s.jsxs("div", { className: "span-legend", children: [
      /* @__PURE__ */ s.jsx("span", { className: "span-legend-word", children: "risk" }),
      a !== null && /* @__PURE__ */ s.jsxs("span", { className: "span-legend-num", children: [
        "τ ",
        a.toFixed(2)
      ] }),
      /* @__PURE__ */ s.jsx("span", { className: "span-legend-bar", "aria-hidden": "true" }),
      /* @__PURE__ */ s.jsx("span", { className: "span-legend-num", children: "1.00" })
    ] })
  ] });
}
function Bf({ result: u }) {
  var x, E, L, T, R;
  const a = (x = u.spans) != null && x.length ? u.spans : (u.segments ?? []).filter((w) => w.verdict === !0).map((w) => ({ text: w.text, startCodePoint: w.startCodePoint, endCodePoint: w.endCodePoint, score: w.score, scoreKind: u.scoreSemantics, verdict: "suspect" })), c = u.categories ?? (Array.isArray(u.classes) ? u.classes : Object.entries(u.classes ?? {}).map(([w, B]) => ({ label: w, score: B })));
  return !(a.length || (E = u.claims) != null && E.length || c.length || u.rationale || (L = u.values) != null && L.length) ? null : /* @__PURE__ */ s.jsxs("details", { className: "evidence-details", children: [
    /* @__PURE__ */ s.jsx("summary", { children: "Evidence details" }),
    a.length ? /* @__PURE__ */ s.jsx("div", { className: "evidence-list", "aria-label": "Suspect spans", children: a.map((w, B) => /* @__PURE__ */ s.jsxs("article", { children: [
      /* @__PURE__ */ s.jsxs("div", { children: [
        /* @__PURE__ */ s.jsx("b", { children: w.text }),
        /* @__PURE__ */ s.jsx("small", { children: w.startCodePoint !== void 0 ? `Characters ${w.startCodePoint}–${w.endCodePoint}` : "Span evidence" })
      ] }),
      /* @__PURE__ */ s.jsxs("span", { children: [
        on(w.score) !== null ? sc(on(w.score)) : zr(w.score, w.scoreKind),
        " · ",
        w.verdict ?? "scored"
      ] })
    ] }, `${w.startCodePoint}-${B}`)) }) : null,
    (T = u.claims) != null && T.length ? /* @__PURE__ */ s.jsx("div", { className: "claim-list", children: u.claims.map((w, B) => /* @__PURE__ */ s.jsxs("article", { className: Al(w.verdict), children: [
      /* @__PURE__ */ s.jsx(ac, { status: w.supported === !0 ? "safe" : w.supported === !1 ? "risk" : w.verdict }),
      /* @__PURE__ */ s.jsxs("div", { children: [
        /* @__PURE__ */ s.jsx("b", { children: w.text ?? w.claim ?? `Claim ${B + 1}` }),
        w.rationale && /* @__PURE__ */ s.jsx("p", { children: w.rationale })
      ] }),
      /* @__PURE__ */ s.jsx("span", { children: w.verdict ?? zr(w.score) })
    ] }, B)) }) : null,
    c.length ? /* @__PURE__ */ s.jsx("div", { className: "class-list", "aria-label": "Class scores", children: c.map((w) => /* @__PURE__ */ s.jsxs("div", { children: [
      /* @__PURE__ */ s.jsx("span", { children: kn(w.label) }),
      /* @__PURE__ */ s.jsx("i", { children: /* @__PURE__ */ s.jsx("b", { style: { width: `${Math.max(0, Math.min(100, w.score * 100))}%` } }) }),
      /* @__PURE__ */ s.jsx("strong", { children: zr(w.score, "categorical_probabilities") })
    ] }, w.label)) }) : null,
    (R = u.values) != null && R.length ? /* @__PURE__ */ s.jsxs(s.Fragment, { children: [
      /* @__PURE__ */ s.jsx("div", { className: "mini-bars", "aria-hidden": "true", children: u.values.map((w, B) => /* @__PURE__ */ s.jsx("i", { style: { height: `${10 + Math.max(0, Math.min(1, w)) * 54}px` } }, B)) }),
      /* @__PURE__ */ s.jsx("ol", { className: "sr-only", "aria-label": "Relative token scores", children: u.values.map((w, B) => /* @__PURE__ */ s.jsxs("li", { children: [
        "Item ",
        B + 1,
        ": ",
        w.toFixed(3)
      ] }, B)) })
    ] }) : null,
    (u.rationale || u.note) && /* @__PURE__ */ s.jsx("p", { className: "rationale", children: u.rationale ?? u.note })
  ] });
}
function Xf({ run: u }) {
  const a = u.provenance ?? {}, c = u.origin === rc, y = c && typeof a.integritySha256 == "string" ? a.integritySha256 : null, x = Object.entries(a).filter(([E, L]) => E !== (y ? "integritySha256" : "") && (typeof L == "string" || typeof L == "number" || typeof L == "boolean"));
  return /* @__PURE__ */ s.jsxs("div", { className: "provenance", children: [
    /* @__PURE__ */ s.jsx("span", { children: c ? "Recorded result · verified" : kn(u.origin ?? u.mode ?? "live run") }),
    (u.setupSnapshot ?? u.setup) && /* @__PURE__ */ s.jsx("span", { children: Hl(u.setupSnapshot ?? u.setup, "detectorPreset", "detectorLabel") }),
    u.staleSetup && /* @__PURE__ */ s.jsx("span", { className: "warning", children: "Different setup" }),
    u.sourceRunId && /* @__PURE__ */ s.jsxs("span", { children: [
      "Source ",
      u.sourceRunId
    ] }),
    y && /* @__PURE__ */ s.jsxs("span", { title: y, children: [
      "Checkpoint ",
      y.slice(0, 12),
      "…"
    ] }),
    x.slice(0, 3).map(([E, L]) => /* @__PURE__ */ s.jsxs("span", { children: [
      kn(E),
      ": ",
      String(L)
    ] }, E))
  ] });
}
function cc({ run: u, motion: a, onAction: c, onPrepareRerun: y }) {
  var Ze, Ae, $e, We;
  const x = u.analysis ?? u.result ?? {}, E = x.scoreSemantics ?? u.scoreSemantics, L = x.score ?? x.confidence ?? u.score, T = Wf(E, x.scaleLabel ?? u.scaleLabel), R = (x.segments ?? []).some((ee) => on(ee.score) !== null || ee.verdict === !0), w = x.verdict ?? u.verdict, B = x.label ?? (typeof w == "string" ? w : null) ?? (u.status === "failed" ? "Failed" : "Result"), A = u.origin === rc, Z = !A && /replay|recorded/i.test(`${u.origin ?? ""} ${u.mode ?? ""}`), oe = ((Ze = globalThis.matchMedia) == null ? void 0 : Ze.call(globalThis, "(prefers-reduced-motion: reduce)").matches) ?? !1, [ce] = ge.useState(() => {
    const ee = !$a.has(u.id);
    return $a.add(u.id), ee;
  }), K = a !== "static" && !oe && ce, V = Z && K, [re, Ee] = ge.useState(!V), Ne = on(x.threshold), de = (x.segments ?? []).filter((ee) => ql(on(ee.score), ee.verdict, Ne)).length, X = R && K, fe = lc + de * ic + Ff, Se = typeof u.error == "string" ? u.error : (Ae = u.error) == null ? void 0 : Ae.message, ye = u.error && typeof u.error == "object" ? u.error : null;
  return /* @__PURE__ */ s.jsxs("section", { className: `result-card ${Al(w ?? B)}${X ? " is-reveal" : ""}`, style: X ? { "--reveal-total": `${fe}ms` } : void 0, "aria-live": "polite", children: [
    /* @__PURE__ */ s.jsxs("div", { className: "result-heading", children: [
      /* @__PURE__ */ s.jsxs("div", { children: [
        /* @__PURE__ */ s.jsx("p", { className: "eyebrow", children: "Outcome" }),
        /* @__PURE__ */ s.jsx("h2", { children: B }),
        /* @__PURE__ */ s.jsx("p", { children: x.summary ?? (u.status === "partial" ? "The answer was preserved, but part of analysis did not complete." : "Evidence is shown in the answer and details below.") })
      ] }),
      !R && on(L) !== null && T && /* @__PURE__ */ s.jsxs("div", { className: "score-orb", children: [
        /* @__PURE__ */ s.jsx("strong", { children: zr(L, E) }),
        /* @__PURE__ */ s.jsx("span", { children: T })
      ] })
    ] }),
    /* @__PURE__ */ s.jsxs("div", { className: "answer-block", children: [
      /* @__PURE__ */ s.jsxs("div", { className: "answer-label", children: [
        /* @__PURE__ */ s.jsx("span", { children: "Answer" }),
        /* @__PURE__ */ s.jsx("small", { children: A ? Pf.recordedResultVerified : Z ? "Recorded answer · live detection" : u.origin === "importedSnapshot" || u.origin === "imported" ? "Imported snapshot" : /answerability/i.test(u.origin ?? u.mode ?? "") ? "Answerability · live detection" : /supplied/i.test(u.origin ?? u.mode ?? "") ? "Supplied answer · live detection" : "Generated now" })
      ] }),
      V && !re ? /* @__PURE__ */ s.jsx(Hf, { answer: u.answer ?? "", onComplete: () => Ee(!0) }) : /* @__PURE__ */ s.jsxs(s.Fragment, { children: [
        /* @__PURE__ */ s.jsx(qf, { answer: u.answer ?? "", result: x }),
        R && /* @__PURE__ */ s.jsx(Af, { result: x })
      ] })
    ] }),
    x.unavailableReason && /* @__PURE__ */ s.jsxs("div", { className: "inline-notice warning", children: [
      /* @__PURE__ */ s.jsx("b", { children: "Analysis unavailable" }),
      /* @__PURE__ */ s.jsx("span", { children: x.unavailableReason })
    ] }),
    Se && /* @__PURE__ */ s.jsxs("div", { className: "inline-notice error", children: [
      /* @__PURE__ */ s.jsx("b", { children: u.status === "partial" ? "Detection did not finish" : "Run failed" }),
      /* @__PURE__ */ s.jsx("span", { children: Se }),
      (ye == null ? void 0 : ye.correlationId) && !Mf.has(ye.code ?? "") && /* @__PURE__ */ s.jsxs("small", { children: [
        "Reference ",
        ye.correlationId
      ] })
    ] }),
    ($e = u.warnings) == null ? void 0 : $e.map((ee, ze) => /* @__PURE__ */ s.jsx("div", { className: "inline-notice warning", children: ee }, ze)),
    /* @__PURE__ */ s.jsx(Bf, { result: x }),
    /* @__PURE__ */ s.jsx(Xf, { run: u }),
    /* @__PURE__ */ s.jsxs("div", { className: "result-actions", children: [
      A && ((We = u.inputs) == null ? void 0 : We.exampleId) && /* @__PURE__ */ s.jsxs("button", { type: "button", className: "primary", title: "Replays the verified answer and runs the probe live. Loads the model.", onClick: () => {
        var ee, ze, De;
        return c("submit", { task: "faithfulness", mode: "recordedReplay", context: ((ee = u.inputs) == null ? void 0 : ee.context) ?? "", question: ((ze = u.inputs) == null ? void 0 : ze.question) ?? "", suppliedAnswer: u.answer ?? "", prompt: "", exampleId: (De = u.inputs) == null ? void 0 : De.exampleId });
      }, children: [
        /* @__PURE__ */ s.jsx(wn, { name: "spark" }),
        "Run it live"
      ] }),
      (u.status === "partial" || u.status === "failed") && u.answer && /* @__PURE__ */ s.jsx("button", { type: "button", className: "secondary", onClick: () => c("retryDetection", { runId: u.id }), children: "Retry detection" }),
      (u.origin === "importedSnapshot" || u.origin === "imported" || u.immutable) && /* @__PURE__ */ s.jsx("button", { type: "button", className: "secondary", onClick: () => y(u), children: "Rerun with current setup" }),
      /* @__PURE__ */ s.jsxs("button", { type: "button", className: "quiet", onClick: () => c("exportRun", { runId: u.id }), children: [
        /* @__PURE__ */ s.jsx(wn, { name: "download" }),
        "Export run"
      ] })
    ] })
  ] });
}
function Zf({ payload: u, draft: a, setDraft: c, busy: y, motion: x, onAction: E, onPrepareRerun: L }) {
  var de;
  const T = u.capabilities ?? {}, R = T, w = String(((de = u.setup) == null ? void 0 : de.task) ?? "faithfulness"), B = w === a.task ? !0 : { enabled: !1, reason: `The active detector supports ${kn(w)}, not ${kn(a.task)}.` }, A = a.task === "answerability" ? R.canAnswerability ?? B : B, Z = a.task === "faithfulness" && a.mode === "generate" ? T.canGenerate : !0, oe = a.prompt.trim().length > 0 || a.context.trim().length > 0 && a.question.trim().length > 0, ce = Ie(A) && Ie(Z) && oe && (a.task === "answerability" || a.mode === "generate" || a.answer.trim().length > 0), K = u.examples ?? [], V = K.find((X) => X.id === a.exampleId), re = !!(V && (V.recordedAnswer || V.answer)), Ee = (X) => c({
    task: X.task ?? a.task,
    mode: a.mode,
    exampleId: X.id,
    context: X.context ?? "",
    question: X.question ?? "",
    answer: X.answer ?? X.recordedAnswer ?? "",
    prompt: X.prompt ?? "",
    sourceRunId: null
  }, !0), Ne = (X) => {
    if (X.preventDefault(), !ce || y) return;
    const fe = a.task === "answerability" ? "answerability" : a.sourceRunId && a.prompt && !a.context && !a.question ? "quickPrompt" : a.mode === "generate" ? "generateAndScore" : "scoreSuppliedAnswer";
    E("submit", {
      task: a.task,
      mode: fe,
      context: a.context,
      question: a.question,
      suppliedAnswer: a.mode === "supplied" ? a.answer : "",
      prompt: a.prompt,
      exampleId: a.exampleId,
      ...a.sourceRunId ? { sourceRunId: a.sourceRunId } : {}
    }), a.sourceRunId && c({ ...a, sourceRunId: null });
  };
  return /* @__PURE__ */ s.jsxs("main", { className: "workspace-content analyze-workspace", children: [
    /* @__PURE__ */ s.jsx(Vf, { examples: K.filter((X) => !X.task || X.task === a.task), selected: a.exampleId, onSelect: Ee }),
    /* @__PURE__ */ s.jsxs("form", { className: "analysis-form", onSubmit: Ne, children: [
      /* @__PURE__ */ s.jsxs("div", { className: "form-row", children: [
        /* @__PURE__ */ s.jsx(pt, { label: "Task", children: /* @__PURE__ */ s.jsxs(Bo, { value: a.task, onChange: (X) => {
          const fe = X.target.value;
          c({ ...a, task: fe, mode: fe === "answerability" ? "generate" : a.mode }, !0);
        }, children: [
          /* @__PURE__ */ s.jsx("option", { value: "faithfulness", disabled: w !== "faithfulness", children: "Faithfulness" }),
          /* @__PURE__ */ s.jsx("option", { value: "answerability", disabled: !Ie(R.canAnswerability ?? w === "answerability"), children: "Answerability" })
        ] }) }),
        a.task === "faithfulness" && /* @__PURE__ */ s.jsx(pt, { label: "Answer source", children: /* @__PURE__ */ s.jsxs(Bo, { value: a.mode, onChange: (X) => c({ ...a, mode: X.target.value }, !0), children: [
          /* @__PURE__ */ s.jsx("option", { value: "generate", disabled: !Ie(T.canGenerate), children: "Generate an answer" }),
          /* @__PURE__ */ s.jsx("option", { value: "supplied", children: "Score supplied answer" })
        ] }) })
      ] }),
      a.prompt && /* @__PURE__ */ s.jsxs("details", { className: "prompt-disclosure", children: [
        /* @__PURE__ */ s.jsxs("summary", { children: [
          /* @__PURE__ */ s.jsx("svg", { className: "disclosure-chevron", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: "1.8", strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": "true", children: /* @__PURE__ */ s.jsx("path", { d: "m9 18 6-6-6-6" }) }),
          /* @__PURE__ */ s.jsx("span", { children: "Exact model prompt" }),
          /* @__PURE__ */ s.jsxs("span", { className: "disclosure-count", children: [
            a.prompt.length.toLocaleString(),
            " characters"
          ] })
        ] }),
        /* @__PURE__ */ s.jsx(pt, { label: "Prompt", children: /* @__PURE__ */ s.jsx("textarea", { rows: 5, value: a.prompt, placeholder: "Verified example or imported prompt…", onChange: (X) => c({ ...a, prompt: X.target.value, exampleId: null }), onBlur: () => c(a, !0) }) })
      ] }),
      /* @__PURE__ */ s.jsx(pt, { label: "Context", hint: `${a.context.length.toLocaleString()} characters`, children: /* @__PURE__ */ s.jsx("textarea", { rows: 7, value: a.context, placeholder: "Paste the source material the answer must stay grounded in…", onChange: (X) => c({ ...a, context: X.target.value }), onBlur: () => c(a, !0) }) }),
      /* @__PURE__ */ s.jsx(pt, { label: "Question", children: /* @__PURE__ */ s.jsx("textarea", { rows: 2, value: a.question, placeholder: "What should the model answer from this context?", onChange: (X) => c({ ...a, question: X.target.value }), onBlur: () => c(a, !0) }) }),
      a.task === "faithfulness" && a.mode === "supplied" && /* @__PURE__ */ s.jsx(pt, { label: "Answer to score", children: /* @__PURE__ */ s.jsx("textarea", { rows: 4, value: a.answer, placeholder: "Paste the answer that should be checked…", onChange: (X) => c({ ...a, answer: X.target.value }), onBlur: () => c(a, !0) }) }),
      !Ie(A) && /* @__PURE__ */ s.jsx("p", { className: "field-error", children: tc(A) ?? "The active detector does not support this task." }),
      !Ie(Z) && /* @__PURE__ */ s.jsx("p", { className: "field-error", children: tc(Z) ?? "Generation is not available with the active setup." }),
      a.sourceRunId && /* @__PURE__ */ s.jsxs("div", { className: "inline-notice info", children: [
        /* @__PURE__ */ s.jsx("b", { children: "Imported run prepared" }),
        /* @__PURE__ */ s.jsx("span", { children: "Review these inputs, then submit explicitly with the current setup." })
      ] }),
      /* @__PURE__ */ s.jsxs("div", { className: "form-actions", children: [
        re && /* @__PURE__ */ s.jsxs("button", { type: "button", className: "primary", disabled: y, onClick: () => E("submit", { task: (V == null ? void 0 : V.task) ?? "faithfulness", mode: "recordedReplay", context: a.context, question: a.question, suppliedAnswer: (V == null ? void 0 : V.recordedAnswer) ?? (V == null ? void 0 : V.answer) ?? "", prompt: "", exampleId: V == null ? void 0 : V.id }), children: [
          /* @__PURE__ */ s.jsx(wn, { name: "spark" }),
          "Replay recorded answer"
        ] }),
        /* @__PURE__ */ s.jsxs("button", { className: re ? "secondary" : "primary", type: "submit", disabled: !ce || y, children: [
          /* @__PURE__ */ s.jsx(wn, { name: "spark" }),
          a.task === "answerability" ? "Check answerability" : a.mode === "supplied" ? "Score answer" : "Generate & score"
        ] })
      ] })
    ] }),
    y ? /* @__PURE__ */ s.jsx(Zo, { activity: u.activity, runs: u.runs ?? [] }) : u.selectedRun ? /* @__PURE__ */ s.jsx(cc, { run: u.selectedRun, motion: x, onAction: E, onPrepareRerun: L }, u.selectedRun.id) : /* @__PURE__ */ s.jsxs("section", { className: "result-placeholder", children: [
      /* @__PURE__ */ s.jsx("div", { children: /* @__PURE__ */ s.jsx(wn, { name: "spark" }) }),
      /* @__PURE__ */ s.jsx("h2", { children: "Your evidence map will appear here." }),
      /* @__PURE__ */ s.jsx("p", { children: "Results lead with the outcome, then reveal only the detail each detector can honestly support." })
    ] })
  ] });
}
function Jf(u) {
  if (!u) return "Time unavailable";
  const a = new Date(u);
  return Number.isNaN(a.valueOf()) ? u : new Intl.DateTimeFormat(void 0, { dateStyle: "medium", timeStyle: "short" }).format(a);
}
function Kf({ runs: u, selectedId: a, onSelect: c, onAnalyze: y }) {
  const [x, E] = ge.useState(""), [L, T] = ge.useState("all"), R = u.filter((w) => (L === "all" || w.status === L) && `${w.title ?? ""} ${w.question ?? ""} ${w.prompt ?? ""} ${w.answer ?? ""}`.toLowerCase().includes(x.toLowerCase()));
  return /* @__PURE__ */ s.jsxs("section", { className: "run-browser", children: [
    /* @__PURE__ */ s.jsxs("div", { className: "section-heading", children: [
      /* @__PURE__ */ s.jsxs("div", { children: [
        /* @__PURE__ */ s.jsx("p", { className: "eyebrow", children: "History" }),
        /* @__PURE__ */ s.jsxs("h2", { children: [
          u.length,
          " ",
          u.length === 1 ? "run" : "runs"
        ] })
      ] }),
      /* @__PURE__ */ s.jsxs("div", { className: "filters", children: [
        /* @__PURE__ */ s.jsx("input", { type: "search", "aria-label": "Search runs", value: x, placeholder: "Search runs", onChange: (w) => E(w.target.value) }),
        /* @__PURE__ */ s.jsxs(Bo, { ariaLabel: "Filter runs by status", value: L, onChange: (w) => T(w.target.value), children: [
          /* @__PURE__ */ s.jsx("option", { value: "all", children: "All outcomes" }),
          /* @__PURE__ */ s.jsx("option", { value: "succeeded", children: "Succeeded" }),
          /* @__PURE__ */ s.jsx("option", { value: "partial", children: "Partial" }),
          /* @__PURE__ */ s.jsx("option", { value: "failed", children: "Failed" }),
          /* @__PURE__ */ s.jsx("option", { value: "interrupted", children: "Interrupted" })
        ] })
      ] })
    ] }),
    /* @__PURE__ */ s.jsx("div", { className: "run-list", children: R.length ? R.map((w) => /* @__PURE__ */ s.jsxs("button", { type: "button", className: a === w.id ? "selected" : "", onClick: () => c(w), children: [
      /* @__PURE__ */ s.jsx(ac, { status: w.status }),
      /* @__PURE__ */ s.jsxs("span", { children: [
        /* @__PURE__ */ s.jsx("b", { children: w.title ?? w.question ?? w.prompt ?? `Run ${w.id}` }),
        /* @__PURE__ */ s.jsxs("small", { children: [
          Jf(w.completedAt ?? w.createdAt),
          " · ",
          kn(w.task),
          " · ",
          kn(w.status)
        ] })
      ] }),
      /* @__PURE__ */ s.jsx("strong", { children: typeof w.verdict == "boolean" ? w.task === "answerability" ? w.verdict ? "Answerable" : "Unanswerable" : w.verdict ? "Unsupported" : "Supported" : w.verdict ?? zr(w.score, w.scoreSemantics) }),
      /* @__PURE__ */ s.jsx(wn, { name: "arrow" })
    ] }, w.id)) : u.length === 0 ? /* @__PURE__ */ s.jsxs("div", { className: "empty-list", children: [
      "No runs yet — ",
      /* @__PURE__ */ s.jsx("button", { type: "button", className: "empty-link", onClick: y, children: "analyze a case" }),
      " to get started."
    ] }) : /* @__PURE__ */ s.jsx("div", { className: "empty-list", children: "No runs match these filters." }) })
  ] });
}
function Qf({ disabled: u, onImport: a }) {
  const c = ge.useRef(null), [y, x] = ge.useState(""), E = async (L) => {
    if (L) {
      if (L.size > 10 * 1024 * 1024) {
        x("Portable bundles must be 10 MiB or smaller.");
        return;
      }
      x(""), a(await L.text(), L.name), c.current && (c.current.value = "");
    }
  };
  return /* @__PURE__ */ s.jsxs(s.Fragment, { children: [
    /* @__PURE__ */ s.jsx("input", { ref: c, hidden: !0, type: "file", accept: "application/json,.json", onChange: (L) => {
      var T;
      return void E((T = L.target.files) == null ? void 0 : T[0]);
    } }),
    /* @__PURE__ */ s.jsxs("button", { type: "button", className: "secondary", disabled: u, onClick: () => {
      var L;
      return (L = c.current) == null ? void 0 : L.click();
    }, children: [
      /* @__PURE__ */ s.jsx(wn, { name: "upload" }),
      "Import JSON"
    ] }),
    y && /* @__PURE__ */ s.jsx("span", { className: "field-error", role: "alert", children: y })
  ] });
}
function Gf({ payload: u, quickPrompt: a, setQuickPrompt: c, selectedId: y, setSelectedId: x, busy: E, motion: L, onAction: T, onPrepareRerun: R, onAnalyze: w }) {
  var oe, ce, K, V;
  const B = u.runs ?? [], A = u.selectedRun ?? B.find((re) => re.id === y) ?? null, Z = String(((oe = u.setup) == null ? void 0 : oe.task) ?? "faithfulness") === "faithfulness";
  return /* @__PURE__ */ s.jsxs("main", { className: "workspace-content runs-workspace", children: [
    /* @__PURE__ */ s.jsxs("form", { className: "quick-run", onSubmit: (re) => {
      re.preventDefault(), a.trim() && !E && Z && T("submit", { task: "faithfulness", mode: "quickPrompt", context: "", question: "", suppliedAnswer: "", prompt: a, exampleId: null });
    }, children: [
      /* @__PURE__ */ s.jsxs("div", { children: [
        /* @__PURE__ */ s.jsx("p", { className: "eyebrow", children: "Quick run" }),
        /* @__PURE__ */ s.jsx("h2", { children: "Ask without building a thread." }),
        /* @__PURE__ */ s.jsx("p", { children: "Each prompt becomes an independent, auditable run." })
      ] }),
      /* @__PURE__ */ s.jsx(pt, { label: "Prompt", children: /* @__PURE__ */ s.jsx("textarea", { rows: 3, value: a, placeholder: "Ask the active generator…", onChange: (re) => c(re.target.value), onBlur: () => c(a, !0) }) }),
      /* @__PURE__ */ s.jsxs("div", { className: "form-actions", children: [
        /* @__PURE__ */ s.jsxs("button", { type: "submit", className: "primary", title: Z ? void 0 : "Quick Run requires a faithfulness detector.", disabled: !a.trim() || E || !Ie((ce = u.capabilities) == null ? void 0 : ce.canGenerate) || !Z, children: [
          /* @__PURE__ */ s.jsx(wn, { name: "spark" }),
          "Run prompt"
        ] }),
        /* @__PURE__ */ s.jsx(Qf, { disabled: !Ie((K = u.capabilities) == null ? void 0 : K.canImport), onImport: (re) => T("import", { json: re }) }),
        /* @__PURE__ */ s.jsxs("button", { type: "button", className: "quiet", disabled: !B.length || !Ie((V = u.capabilities) == null ? void 0 : V.canExport), onClick: () => T("exportBundle", {}), children: [
          /* @__PURE__ */ s.jsx(wn, { name: "download" }),
          "Export session"
        ] })
      ] })
    ] }),
    E && /* @__PURE__ */ s.jsx(Zo, { activity: u.activity, runs: u.runs ?? [] }),
    /* @__PURE__ */ s.jsxs("div", { className: "runs-grid", children: [
      /* @__PURE__ */ s.jsx(Kf, { runs: B, selectedId: (A == null ? void 0 : A.id) ?? y, onSelect: (re) => {
        x(re.id), T("selectRun", { runId: re.id });
      }, onAnalyze: w }),
      /* @__PURE__ */ s.jsx("aside", { className: "run-detail", children: A ? /* @__PURE__ */ s.jsx(cc, { run: A, motion: L, onAction: T, onPrepareRerun: R }, A.id) : /* @__PURE__ */ s.jsxs("div", { className: "result-placeholder compact", children: [
        /* @__PURE__ */ s.jsx("h2", { children: "Select a run" }),
        /* @__PURE__ */ s.jsx("p", { children: "Its outcome, evidence, and provenance will appear here." })
      ] }) })
    ] })
  ] });
}
function Yf(u) {
  return u ? Array.isArray(u) ? u : Object.entries(u).map(([a, c]) => ({ label: kn(a), value: typeof c == "object" ? JSON.stringify(c) : c })) : [];
}
function _f({ diagnostics: u }) {
  var c;
  const a = u == null ? void 0 : u.attention;
  return (c = a == null ? void 0 : a.values) != null && c.length ? /* @__PURE__ */ s.jsxs("section", { className: "attention-card", children: [
    /* @__PURE__ */ s.jsx("div", { className: "section-heading", children: /* @__PURE__ */ s.jsxs("div", { children: [
      /* @__PURE__ */ s.jsx("p", { className: "eyebrow", children: "Attention" }),
      /* @__PURE__ */ s.jsx("h2", { children: a.title ?? "Bounded attention summary" })
    ] }) }),
    /* @__PURE__ */ s.jsx("div", { className: "table-scroll", children: /* @__PURE__ */ s.jsxs("table", { children: [
      /* @__PURE__ */ s.jsx("thead", { children: /* @__PURE__ */ s.jsxs("tr", { children: [
        /* @__PURE__ */ s.jsx("th", { children: "Token" }),
        (a.columnLabels ?? []).map((y) => /* @__PURE__ */ s.jsx("th", { children: y }, y))
      ] }) }),
      /* @__PURE__ */ s.jsx("tbody", { children: a.values.map((y, x) => {
        var E;
        return /* @__PURE__ */ s.jsxs("tr", { children: [
          /* @__PURE__ */ s.jsx("th", { children: ((E = a.rowLabels) == null ? void 0 : E[x]) ?? x + 1 }),
          y.map((L, T) => /* @__PURE__ */ s.jsx("td", { style: L === null ? void 0 : { "--attention": String(Math.max(0, Math.min(1, L))) }, children: /* @__PURE__ */ s.jsx("span", { children: L === null ? "—" : L.toFixed(2) }) }, T))
        ] }, x);
      }) })
    ] }) }),
    a.note && /* @__PURE__ */ s.jsx("p", { className: "caption", children: a.note })
  ] }) : /* @__PURE__ */ s.jsxs("div", { className: "result-placeholder compact", children: [
    /* @__PURE__ */ s.jsx("h2", { children: "No attention summary yet" }),
    /* @__PURE__ */ s.jsx("p", { children: "Attention summaries appear here when the active detector captures them." })
  ] });
}
function bf({ payload: u, busy: a, onAction: c }) {
  var T;
  const y = u.diagnostics, x = u.capabilities ?? {}, E = y != null && y.metrics ? Yf(y.metrics) : [
    { label: "Runtime", value: (y == null ? void 0 : y.runtime) ?? "Python" },
    { label: "Device", value: (y == null ? void 0 : y.device) ?? "Loads on first run" },
    { label: "Model", value: (y == null ? void 0 : y.activeModel) ?? (y != null && y.modelLoaded ? "Loaded" : "Loads on first run") },
    { label: "Attention", value: y != null && y.attentionAvailable ? "Available" : "Not captured in this mode" }
  ], L = !!((T = u.capabilities) != null && T.trustedLocal);
  return /* @__PURE__ */ s.jsxs("main", { className: "workspace-content diagnostics-workspace", children: [
    !L && /* @__PURE__ */ s.jsx("div", { className: "privacy-banner", children: /* @__PURE__ */ s.jsxs("div", { children: [
      /* @__PURE__ */ s.jsx("b", { children: "Shared-safe diagnostics" }),
      /* @__PURE__ */ s.jsx("span", { children: "Sensitive paths, traces, provider responses, and raw runtime errors remain hidden." })
    ] }) }),
    a && /* @__PURE__ */ s.jsx(Zo, { activity: u.activity, runs: u.runs ?? [] }),
    L && (Ie(x.canRefreshDiagnostics, !1) || Ie(x.canOpenCachedAttention, !1) || Ie(x.canOpenLiveAttention, !1) || Ie(x.canUnloadModels, !1)) && /* @__PURE__ */ s.jsxs("div", { className: "diagnostic-actions", children: [
      Ie(x.canRefreshDiagnostics, !1) && /* @__PURE__ */ s.jsx("button", { type: "button", className: "secondary", disabled: a, onClick: () => c("refreshDiagnostics", {}), children: "Refresh runtime" }),
      Ie(x.canOpenCachedAttention, !1) && /* @__PURE__ */ s.jsx("button", { type: "button", className: "secondary", disabled: a, onClick: () => c("openCachedAttention", {}), children: "Cached attention explorer" }),
      Ie(x.canOpenLiveAttention, !1) && /* @__PURE__ */ s.jsx("button", { type: "button", className: "secondary", disabled: a, onClick: () => c("openLiveAttention", {}), children: "Live attention capture" }),
      Ie(x.canUnloadModels, !1) && /* @__PURE__ */ s.jsx("button", { type: "button", className: "quiet", disabled: a, onClick: () => c("unloadModels", {}), children: "Unload models" })
    ] }),
    /* @__PURE__ */ s.jsx("section", { className: "metric-grid", children: E.length ? E.map((R) => /* @__PURE__ */ s.jsxs("article", { className: Al(R.status), children: [
      /* @__PURE__ */ s.jsx("span", { children: R.label }),
      /* @__PURE__ */ s.jsx("strong", { children: R.value === null ? "Not captured in this mode" : String(R.value) }),
      R.detail && /* @__PURE__ */ s.jsx("small", { children: R.detail })
    ] }, R.label)) : /* @__PURE__ */ s.jsxs("article", { children: [
      /* @__PURE__ */ s.jsx("span", { children: "Runtime status" }),
      /* @__PURE__ */ s.jsx("strong", { children: (y == null ? void 0 : y.status) ?? "Ready" }),
      /* @__PURE__ */ s.jsx("small", { children: "Refresh to request a safe server summary." })
    ] }) }),
    (y == null ? void 0 : y.message) && /* @__PURE__ */ s.jsx("div", { className: "inline-notice info", children: y.message }),
    /* @__PURE__ */ s.jsx(_f, { diagnostics: y }),
    L && (y == null ? void 0 : y.details) && /* @__PURE__ */ s.jsxs("details", { className: "diagnostic-details", children: [
      /* @__PURE__ */ s.jsx("summary", { children: "Trusted-local details" }),
      /* @__PURE__ */ s.jsx("dl", { children: Object.entries(y.details).map(([R, w]) => /* @__PURE__ */ s.jsxs("div", { children: [
        /* @__PURE__ */ s.jsx("dt", { children: kn(R) }),
        /* @__PURE__ */ s.jsx("dd", { children: typeof w == "object" ? JSON.stringify(w) : String(w) })
      ] }, R)) })
    ] })
  ] });
}
function $f(u) {
  try {
    const a = URL.createObjectURL(new Blob([u.content], { type: u.mimeType ?? "application/json" })), c = document.createElement("a");
    return c.href = a, c.download = u.fileName, c.click(), URL.revokeObjectURL(a), !0;
  } catch {
    return !1;
  }
}
function ep({ componentKey: u, payload: a, setStateValue: c, setTriggerValue: y }) {
  var Ae, $e, We, ee, ze, De, Oe, se;
  const x = a.viewState, E = Ul.get(u) ?? { sequence: 0, draft: If(a.draft), workspace: (x == null ? void 0 : x.workspace) ?? "analyze", appearance: (x == null ? void 0 : x.appearance) ?? Of, selectedRunId: null, seenDownload: null, focusWorkspace: null };
  Ul.has(u) || Ul.set(u, E);
  const [L, T] = ge.useState(E.workspace), [R, w] = ge.useState(E.appearance), [B, A] = ge.useState(E.draft), [Z, oe] = ge.useState(E.selectedRunId), [ce, K] = ge.useState(!1), V = ge.useRef(null), re = (Ae = a.actionReceipt) == null ? void 0 : Ae.sequence;
  ge.useEffect(() => K(!1), [re, ($e = a.activity) == null ? void 0 : $e.status, a.runsRevision]), ge.useEffect(() => {
    x != null && x.workspace && x.workspace !== E.workspace && (E.workspace = x.workspace, T(x.workspace)), x != null && x.appearance && (x.appearance.theme !== E.appearance.theme || x.appearance.motion !== E.appearance.motion) && (E.appearance = x.appearance, w(x.appearance));
  }, [x == null ? void 0 : x.workspace, (We = x == null ? void 0 : x.appearance) == null ? void 0 : We.theme, (ee = x == null ? void 0 : x.appearance) == null ? void 0 : ee.motion, E]), ge.useEffect(() => {
    document.documentElement.dataset.sirinMotion = R.motion;
  }, [R.motion]), ge.useEffect(() => {
    var P;
    const k = E.focusWorkspace;
    if (!k || (x == null ? void 0 : x.workspace) !== k) return;
    const F = (P = V.current) == null ? void 0 : P.querySelector(`[data-workspace-tab="${k}"]`);
    F && (F.focus(), E.focusWorkspace = null);
  }, [x == null ? void 0 : x.workspace, E]), ge.useEffect(() => {
    if (!a.download) {
      E.seenDownload = null;
      return;
    }
    const k = a.download ? `${a.download.fileName}:${a.download.content.length}` : null;
    if (a.download && k !== E.seenDownload && (E.seenDownload = k, $f(a.download))) {
      E.sequence += 1;
      const F = { protocolVersion: a.protocolVersion, clientInstanceId: ec(), sequence: E.sequence, actionId: nc(), type: "clearDownload", expectedSetupRevision: a.setupRevision, expectedRunsRevision: a.runsRevision, payload: {} };
      y("action", F);
    }
  }, [a.download, a.protocolVersion, a.setupRevision, a.runsRevision, E, y]);
  const Ee = ce || ["queued", "running"].includes(((ze = a.activity) == null ? void 0 : ze.status) ?? ""), Ne = (k) => {
    E.workspace = k, E.focusWorkspace = k, T(k), y("viewState", { workspace: k, appearance: E.appearance });
  }, de = (k, F = !1) => {
    const P = { ...B, analyze: k };
    E.draft = P, A(P), F && c("draft", P);
  }, X = (k, F = !1) => {
    const P = { ...B, quickPrompt: k };
    E.draft = P, A(P), F && c("draft", P);
  }, fe = (k) => {
    E.selectedRunId = k, oe(k), c("selectedRunId", k);
  }, Se = (k) => {
    var S;
    const F = k.inputs ?? {}, h = { task: ((S = k.setupSnapshot) == null ? void 0 : S.task) ?? k.task ?? "faithfulness", mode: F.suppliedAnswer ? "supplied" : "generate", exampleId: null, context: F.context ?? "", question: F.question ?? "", answer: F.suppliedAnswer ?? "", prompt: F.prompt ?? "", sourceRunId: k.id };
    de(h, !0), Ne("analyze");
  }, ye = (k, F) => {
    if (Ee) return;
    E.sequence += 1;
    const P = { protocolVersion: a.protocolVersion, clientInstanceId: ec(), sequence: E.sequence, actionId: nc(), type: k, expectedSetupRevision: a.setupRevision, expectedRunsRevision: a.runsRevision, payload: F };
    K(!["selectRun"].includes(k)), y("action", P);
  }, Ze = a.notices ?? [];
  return /* @__PURE__ */ s.jsx("div", { ref: V, className: "sirin-workspace", "data-theme": R.theme, "data-motion": R.motion, children: /* @__PURE__ */ s.jsxs("div", { className: "shell", children: [
    /* @__PURE__ */ s.jsx(Df, { workspace: L, onWorkspace: Ne, setup: a.setup, title: (De = a.ui) == null ? void 0 : De.title, subtitle: (Oe = a.ui) == null ? void 0 : Oe.subtitle }),
    Ze.length > 0 && /* @__PURE__ */ s.jsx("div", { className: "notice-stack", "aria-live": "polite", children: Ze.map((k, F) => /* @__PURE__ */ s.jsxs("div", { className: `inline-notice ${k.level ?? k.kind ?? "info"}`, children: [
      k.title && /* @__PURE__ */ s.jsx("b", { children: k.title }),
      /* @__PURE__ */ s.jsx("span", { children: k.message })
    ] }, F)) }),
    ((se = a.actionReceipt) == null ? void 0 : se.status) === "rejected" && /* @__PURE__ */ s.jsxs("div", { className: "inline-notice error receipt", role: "alert", children: [
      /* @__PURE__ */ s.jsx("b", { children: "Action rejected" }),
      /* @__PURE__ */ s.jsx("span", { children: a.actionReceipt.message ?? "The request could not be accepted." })
    ] }),
    L === "analyze" && /* @__PURE__ */ s.jsx(Zf, { payload: a, draft: B.analyze, setDraft: de, busy: Ee, motion: R.motion, onAction: ye, onPrepareRerun: Se }),
    L === "runs" && /* @__PURE__ */ s.jsx(Gf, { payload: a, quickPrompt: B.quickPrompt, setQuickPrompt: X, selectedId: Z, setSelectedId: fe, busy: Ee, motion: R.motion, onAction: ye, onPrepareRerun: Se, onAnalyze: () => Ne("analyze") }),
    L === "diagnostics" && /* @__PURE__ */ s.jsx(bf, { payload: a, busy: Ee, onAction: ye }),
    /* @__PURE__ */ s.jsxs("footer", { children: [
      /* @__PURE__ */ s.jsx("span", { children: "SIRIN" }),
      /* @__PURE__ */ s.jsx("span", { children: "Detector confidence is not automatically a calibrated probability." })
    ] })
  ] }) });
}
const Nr = /* @__PURE__ */ new WeakMap(), Cr = /* @__PURE__ */ new Map();
function np(u) {
  for (const [a, c] of Cr)
    a !== u && !c.isConnected && (Ul.delete(a), Cr.delete(a));
}
const tp = ({ data: u, key: a, parentElement: c, setStateValue: y, setTriggerValue: x }) => {
  Lf(), Tf(c);
  let E = Nr.get(c);
  if (E && (!E.container.isConnected || E.container.parentNode !== c)) {
    try {
      E.root.unmount();
    } catch {
    }
    E.container.remove(), Nr.delete(c), E = void 0;
  }
  if (!E) {
    c.querySelectorAll(".sirin-component-root").forEach((R) => R.remove());
    const T = document.createElement("div");
    T.className = "sirin-component-root", c.append(T), E = { container: T, root: vf.createRoot(T) }, Nr.set(c, E);
  }
  Cr.set(a, E.container), np(a);
  const L = E;
  return L.root.render(/* @__PURE__ */ s.jsx(ep, { componentKey: a, payload: u, setStateValue: y, setTriggerValue: x })), () => {
    Nr.get(c) === L && (Nr.delete(c), Cr.get(a) === L.container && Cr.delete(a), L.root.unmount(), L.container.remove());
  };
};
export {
  tp as default
};
